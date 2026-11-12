"""Adaptadores de análisis real con contrato común de tokens y POS."""
import importlib.metadata
import re
from time import perf_counter
import unicodedata
from minic.grammar import Grammar
from minic.parser import parse_detailed
from minic.trees import bracketed
from .common import ROOT, digest


def coarse_pos(tag):
    return {'AUX': 'VERB', 'PROPN': 'NOUN'}.get(tag, tag)


def token_pos(token_type):
    if token_type.startswith('DET_'):
        return 'DET'
    if token_type.startswith('SUST_'):
        return 'NOUN'
    if token_type.startswith('ADJ_'):
        return 'ADJ'
    if token_type.startswith(('VERB_', 'COP_')):
        return 'VERB'
    return {'ADV': 'ADV', 'PREP': 'ADP', 'QUE': 'SCONJ',
            'CONJ_Y': 'CCONJ', 'NUM': 'NUM'}.get(token_type, 'X')


class OwnParser:
    def __init__(self):
        self.grammar = Grammar(ROOT / 'gramatica_minic.txt')
        self.info = dict(tool='parser', model='CFG LL(1)', version=digest(ROOT / 'gramatica_minic.txt'))

    def analyze(self, text):
        result = parse_detailed(text, self.grammar, True)
        tokens = [token for token in result.tokens if token[0] != '$']
        positions = {(token[2], token[3]): token[0] for token in tokens}
        words, tags = [], []
        for match in re.finditer(r'[^\W\d_]+|[^\w\s]', text, re.UNICODE):
            line = text.count('\n', 0, match.start()) + 1
            column = match.start() - text.rfind('\n', 0, match.start())
            words.append(match.group())
            tags.append(token_pos(positions.get((line, column), 'ID')))
        return dict(tokens=words, pos=tags, lexical_tokens=tokens,
                    accepted=result.accepted, tree=bracketed(result.tree),
                    diagnostics=[d.to_dict() for d in result.diagnostics],
                    productions=result.productions)


def eagles_pos(tag):
    if tag.startswith('cs'):
        return 'SCONJ'
    return dict(a='ADJ', d='DET', n='NOUN', v='VERB', r='ADV',
                s='ADP', c='CCONJ', p='PRON', z='NUM', f='PUNCT', i='INTJ').get(tag[:1].lower(), 'X')


class NltkSpanish:
    def __init__(self):
        import nltk
        from nltk.corpus import cess_esp
        nltk.data.path.insert(0, str(ROOT / '.models/nltk'))
        sentences = [[(unicodedata.normalize('NFC', word).lower(), eagles_pos(tag))
                      for word, tag in sentence] for sentence in cess_esp.tagged_sents()]
        fallback = nltk.DefaultTagger('NOUN')
        suffix = nltk.AffixTagger(sentences, affix_length=-3, backoff=fallback)
        self.tagger = nltk.UnigramTagger(sentences, backoff=suffix)
        self.info = dict(tool='nltk', version=nltk.__version__,
                         model='CESS-ESP unigram + sufijos -3 + NOUN',
                         training_sentences=len(sentences),
                         training_tokens=sum(map(len, sentences)),
                         training_sha256=digest(ROOT / '.models/nltk/corpora/cess_esp.zip'))

    def analyze(self, text):
        words = re.findall(r'[^\W\d_]+|[^\w\s]', unicodedata.normalize('NFC', text), re.UNICODE)
        tagged = self.tagger.tag([word.lower() for word in words])
        return dict(tokens=words, pos=[tag for _, tag in tagged], accepted=None)


class SpacySpanish:
    def __init__(self):
        import spacy
        self.nlp = spacy.load('es_core_news_sm')
        self.info = dict(tool='spacy', version=spacy.__version__,
                         model='es_core_news_sm', model_version=importlib.metadata.version('es_core_news_sm'))

    def analyze(self, text):
        doc = self.nlp(unicodedata.normalize('NFC', text))
        tokens = [token for token in doc if not token.is_space]
        return dict(tokens=[t.text for t in tokens], pos=[coarse_pos(t.pos_) for t in tokens],
                    accepted=None, dependencies=[dict(text=t.text, head=t.head.i, dep=t.dep_,
                                                     lemma=t.lemma_, morph=str(t.morph)) for t in tokens])


ADAPTERS = {'parser': OwnParser, 'nltk': NltkSpanish, 'spacy': SpacySpanish}


def create(name):
    start = perf_counter()
    adapter = ADAPTERS[name]()
    adapter.info['initialization_seconds'] = perf_counter() - start
    return adapter
