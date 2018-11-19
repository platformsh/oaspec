# -*- coding: utf-8 -*-

from pathlib import Path
from pprint import pprint
import pyparsing as pp
from pyparsing import Word, Optional, Literal, LineEnd, Group, Combine, OneOrMore, Or, printables, alphas, ParseResults

pp.ParserElement.setDefaultWhitespaceChars(' \t')

code_fence = Literal("```")
block_start = Combine(code_fence + Optional(Word(alphas)) + "\n")
block_end = Combine(code_fence + LineEnd())
block_line = OneOrMore(Combine(Word(printables) + LineEnd()))
code_block = block_start + pp.SkipTo(block_end) + block_end

h2_header = Combine(pp.LineStart() + Literal("## ") + OneOrMore(Word(printables+' ')) + LineEnd().suppress())
h2_section = h2_header.setResultsName("header") + pp.SkipTo(h2_header).setResultsName("content")


file = Path("/Users/nickanderegg/platform/personal/oaspec/specs/raw-3.0.1.md")
with file.open('r') as f:
    contents = f.read()

results = ParseResults(h2_section.scanString(contents, overlap=False)).asList()
# print(len(results))
# pprint([x for x in results])

for result in results:
    if "Specification" in result[0]["header"]:
        spec_contents = result[0]["content"]

h3_header = Combine(pp.LineStart() + Literal("### ") + OneOrMore(Word(printables+' ')) + LineEnd().suppress())
schema_section = Literal('### Schema\n').setResultsName("header") + pp.SkipTo(h3_header).setResultsName("content")

results = ParseResults(schema_section.scanString(spec_contents, overlap=False)).asList()

schema_def = "{}\n".format(results[0][0]["content"].strip())

object_header = Combine(
    pp.LineStart() +
    Literal("#### <a name=\"") +
    Word(alphas).setResultsName("name") +
    Literal("\"></a>") +
    Combine(OneOrMore(Word(printables+' '))).setResultsName("title") +
    LineEnd().suppress()
)
object_section = object_header + pp.SkipTo(object_header | pp.StringEnd()).setResultsName("content")

results = ParseResults(object_section.scanString(schema_def, overlap=False)).asList()

# for result in results:
#     # print(result[0]["header"])
#     print(result)

# print(len(results))

# pprint(schema_def[results[-1][2]-100:results[-1][2]])

pprint(results[10][0]["content"])

object_description = 
