""" For each word, provide the re pattern for recognizing it and the canonical name for it.
"""
import re
from collections import namedtuple
Reserved = namedtuple('Reserved_Word', 'regex canon')


def canonical(token_str):
  """ If token_str matches a regex, return the canonical value. Otherwise, None
  """
  for word in reserved_words:
    if re.match(word.regex, token_str, re.I):
      return word.canon
  return None


reserved_words = [
    # '^BEGIN$'
    # '^END.$'
    # '^AND$'
    # '^+$'
    # '^OR$'
    # '^,'

    Reserved(r'^(\d[a-z]{2})?CONC$', 'conc'),
    Reserved(r'^(\d[a-z]{2})?MAJOR$', 'major'),
    Reserved(r'(^\d[a-z]{2})?MINOR$', 'minor'),
    Reserved(r'(^\d[a-z]{2})?COLLEGE$', 'college'),
    Reserved('^ACCEPT$', 'accept'),
    Reserved('^ALLBLOCKS$', 'allblocks'),
    Reserved('^ALLOW$', 'allow'),
    Reserved('^AT$', 'at'),
    Reserved('^BEGINSUB$', 'beginsub'),
    Reserved('^BLOCK(S)?$', 'block'),
    Reserved('^BLOCKTYPE(S)?$', 'blocktype'),
    Reserved('^CheckElectiveCreditsAllowed$', 'checkelectivecreditsallowed'),
    Reserved('^CLASS(ES)?$', 'class'),
    Reserved('^COLLEGE$', 'college'),
    Reserved('^COPYRULESFROM$', 'copyrulesfrom'),
    Reserved('^COURSE(S)?$', 'course'),
    Reserved('^CREDIT(S)?$', 'credits'),
    Reserved('^DECIDE$', 'decide'),
    Reserved('^DEGREE$', 'degree'),
    Reserved('^DISPLAY$', 'display'),
    Reserved('^DONTSHARE$', 'dontshare'),
    Reserved('^ELSE$', 'else'),
    Reserved('^ENDSUB$', 'endsub'),
    Reserved('^EXCEPT$', 'except'),
    Reserved('^EXCLUSIVE$', 'exclusive'),
    Reserved('^FROM$', 'from'),
    Reserved('^GROUP(S)?$', 'group'),
    Reserved('^HIDE-?(RULE)?$', 'hide'),
    Reserved('^HIGH-?PRI(ORITY)?$', 'highpri'),
    Reserved('^IF$', 'if'),
    Reserved('^IN$', 'in'),
    Reserved('^INCLUDE-?BLOCKS-?WITH$', 'includeblockswith'),
    Reserved('^INCLUDING$', 'including'),
    Reserved('^LABEL$', 'label'),
    Reserved('^LASTRES(IDENCE)?$', 'lastres'),
    Reserved('^LIBL$', 'libl'),
    Reserved('^LOW-?PRI(ORITY)?$', 'lowpri'),
    Reserved('^LOWEST-?PRI(ORITY)?$', 'lowestpri'),
    Reserved('^MAXCLASS(ES)?$', 'maxclasses'),
    Reserved('^MAXCREDIT(S)?$', 'maxcredits'),
    Reserved('^MAXPASSFAIL$', 'maxpassfail'),
    Reserved('^MAXPERDISC$', 'maxperdisc'),
    Reserved('^MAXSPREAD$', 'maxspread'),
    Reserved('^MAXTERM$', 'maxterm'),
    Reserved('^MAXTRANSFER$', 'maxtransfer'),
    Reserved('^MINAREA(S)?$', 'minarea'),
    Reserved('^MINCLASS(ES)?$', 'minclasses'),
    Reserved('^MINCREDIT(S)?$', 'mincredits'),
    Reserved('^MINGPA$', 'mingpa'),
    Reserved('^MINGRADE$', 'mingrade'),
    Reserved('^MINPERDISC$', 'minperdisc'),
    Reserved('^MINRES$', 'minres'),
    Reserved('^MINSPREAD$', 'minspread'),
    Reserved('^MINTERM$', 'minterm'),
    Reserved('^NOCOUNT$', 'nocount'),
    Reserved('^NONCOURSE(S)?$', 'noncourse'),
    Reserved('^NONEXCLUSIVE$', 'nonexclusive'),
    Reserved('^NOTGPA$', 'notgpa'),
    Reserved('^NUM(BEROF)?CONC(ENTRATION)?S?$', 'numconcs'),
    Reserved('^NUM(BEROF)?MAJOR(S)?$', 'nummajors'),
    Reserved('^NUM(BEROF)?MINOR(S)?$', 'numminors'),
    Reserved('^OPTIONAL$', 'optional'),
    Reserved('^OTHER$', 'other'),
    Reserved('^PROGRAM$', 'program'),
    Reserved('^PROXY-?ADVICE$', 'proxyadvice'),
    Reserved('^PSEUDO$', 'pseudo'),
    Reserved('^REMARK$', 'remark'),
    Reserved('^RULE-?COMPLETE$', 'rulecomplete'),
    Reserved('^RULE-?INCOMPLETE$', 'ruleincomplete'),
    Reserved('^RULETAG$', 'ruletag'),
    Reserved('^SAMEDISC$', 'samedisc'),
    Reserved('^SCHOOL$', 'school'),
    Reserved('^SHAREWITH$', 'sharewith'),
    Reserved('^SPEC$', 'spec'),
    Reserved('^SPMAXCREDIT(S)?$', 'spmaxcredit'),
    Reserved('^SPMAXTERM$', 'spmaxterm'),
    Reserved('^STANDALONEBLOCK$', 'standaloneblock'),
    Reserved('^THEN$', 'then'),
    Reserved('^THISBLOCK$', 'thisblock'),
    Reserved('^UNDER$', 'under'),
    Reserved('^WITH', 'with'),
]

financial_aid_words = [
    Reserved('^CompletedTermCount^CompletedTermCount$', 'completedtermcount'),
    Reserved('^ResidenceCompletedTermCount$', 'residencecompletedtermcount'),
    Reserved('^CreditsAttemptedThisTerm$', 'creditsattemptedthisterm'),
    Reserved('^CreditsEarnedThisTerm$', 'creditsearnedthisterm'),
    Reserved('^CreditsAttemptedThisAidYear$', 'creditsattemptedthisaidyear'),
    Reserved('^CreditsEarnedThisAidYear$', 'creditsearnedthisaidyear'),
    Reserved('^DegreeCreditsRequired$', 'degreecreditsrequired'),
    Reserved('^LastCompletedTermType$', 'lastcompletedtermtype'),
    Reserved('^Previous$', 'previous'),
    Reserved('^Current$', 'current'),
    Reserved('^ResidenceCreditsEarned$', 'residencecreditsearned'),
    Reserved('^TotalCreditsAttempted$', 'totalcreditsattempted'),
    Reserved('^TotalCreditsEarned$', 'totalcreditsearned'),
]
