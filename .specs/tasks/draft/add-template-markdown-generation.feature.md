---
title: Add template-based markdown file generation and manipulation
---

## Initial User Prompt

add template based markdown files generation and manipulation

### Acceptance Criteria

This project need cli tool which is capable of performing following operations:
- extracting structure of a markdown file (all headers and frontmatter) and displaying it in a tree like structure
    - it should also show amount of lines and tokens (approximatly) in the file and per each section
    - it should show list items amount
- extract and show only specific sections content of the file. It should support css like based selectors. For example:
    - `h2#introduction` - show content of the h2 header with id `introduction`, including all subheaders in section
    - `h3#subsection` - show content of the h3 header with id `subsection`, including all subheaders in section
    - `h2#introduction,h3#subsection` - show content of the h2 header with id `introduction` and h3 header with id `subsection`, including all subheaders in section
    - `h2#introduction,h3#subsection` - show content of the h2 header with id `introduction` and h3 header with id `subsection`, including all subheaders in section
    - also add simular selectors for yaml frontmatter. For example:
        - `fm` - show content of the yaml frontmatter
        - `fm.title` - show content of the title property in yaml frontmatter
        - `fm.title,fm.descriptionList[1].name` - show content of the title and description properties in yaml frontmatter
- generating a new markdown file from a template. Template should be also be a markdown or mdx file with section templating support, like handelbars, jade or simular.
- extracting specific sections of a markdown file and injecting them into a new markdown file based on the template (with ability to define which sections to include and which to exclude)
- going through directory and counting all markdown files lines amount and token amount (with ability to define which files to exclude) and save result of folder with per item stats to a file or simply output

### Specific use cases that it should support

- agent should be able to use cli like this: `cli structure some-markdown-file.md` and receive tree structure of the file, to avoid reading it fully. It will get amount of tokens, to decide if it should read the file fully or not.
- agent should be able to use cli like this: `cli read some-markdown-file.md --sections "h2#introduction,h2:other-section"` and receive the content of the sections
- should be possible to integrate to CI pipeline step that run in all `plugins/*/` folders logic that count amount of lines and tokens and save them to each `plugins/**/stats.yaml` file. So it will be visible how big each skill and agent file is
- should be possible to write tempalte markdown files that will be used to generate final makrdown file with ability to inject content from other files. For example:
`sdd/agents/code-quality-reviewer.tmpl.md`
```markdown
# Code Quality Reviewer

{{ @../../agents/base-personality.md }}

## Base judging instructions

{{ @../../sdd/agents/judge.md#base-judging-instructions }}

## Code Quality Rules

{{ @../../ddd/rules/*.md(exclude:#references)}}
```

CRITICAL: exact syntaxis not important, only important supported functionality. Better to reuse some existing solutions, rather than inventing own.

### Researcher requirements

This requirements for researcher only. Make research and create 3 skills for specific task. Your job to find a way to reuse some existing solutions or libraries for this task, instead of writing custom code.
- `markdown-parser` skill - find some existing library that can be used as core for markdown parsing and manipulation. Examples that you can start, but shouldn't stop: https://github.com/mdx-js/mdx, https://github.com/tinacms/tinacms, https://github.com/remarkjs/remark, https://github.com/markdoc/markdoc, https://github.com/vercel/streamdown, https://github.com/flowershow/markdowndb. If there nothing that can be utilized out of the box, find some code in such projects that provide minimal suitable implementation that can be copied and reused.
- `file-token-estimation` skill - find some existing library that can be used to estimate amount of tokens that it will take for LLM to read the file. It should be able to count not only total amount of tokens but sections also. Include in this skill file lenght estimation.
- `makrdown-to-html-selector` skill - research some library that can be used as part of css like selector picking of content. Something simular to what github uses to transform readme files to html with valid selectors. Agents will expect simular results when will try to pick content based on selectors.
- `markdown-template` skill - research some library solution that can be used to create makrdown tempaltes and generate content from them. It should be good enough to integrate with structure based selectors


### Architectual requirements

- Use typescript and nestjs and https://github.com/jmcdo29/nest-commander to create cli tool (nest-commander is criticl and not negotiable)
- use npm init, with name `mdb` (markdown database) to create project
- place code in `src/` folder and unit tests inside of `src/**/__tests__/` folders for each module
- create root tests/ folder that uses bash to test all commands by running tsx agains src and invoking commands as real user would do
- keep proper modules structure in `src/` folder, for example: `src/parser/`, `src/cli` and etc. Cli should be isolated from code, because in future business logic can be published as npm library.
- your job to find a proper way to decrease amount of code that will be written and use existing solutions, that researcher was able to find. if it possible. This project MUST be keept simple and easy to understand and maintain. Each code line counts.

## Description

// Will be filled in future stages by business analyst
