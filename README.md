# United States (Tennessee): law history in git

The law of Tennessee as a git history: one file per provision, with `git blame` and `git log` working line by line. It follows the shared design of [lexifina/global-law](https://github.com/lexifina/global-law).

**What is in it now (a first build, not complete)**

| Folder | Act | Versions | History |
| --- | --- | ---: | --- |
| `constitution-*/` | Constitution of Tennessee, one folder per article (and the preamble, schedule and ordinance) | 18 | 15 folders, 156 provisions, releases 72-76 |
| `title-39-chapter-*/` | Tennessee Code, Title 39: Criminal Offenses, one folder per chapter | 25 | 13 chapters, 741 sections, releases 72-76 |
| `title-48-chapter-*/` | Tennessee Code, Title 48: Corporations, one folder per chapter | 96 | 85 chapters, 1047 sections, releases 72-76 |
| `title-66-chapter-*/` | Tennessee Code, Title 66: Property, one folder per chapter | 49 | 37 chapters, 703 sections, releases 72-76 |

**Source.** The five bulk releases (72 to 76) of the Official Code of Tennessee Annotated that the State issued between 2020-09-01 and 2021-05-21, as [posted on the Internet Archive](https://archive.org/details/gov.tn.tca) by Public.Resource.Org, which is the source of the bytes. English. Only the statute text is taken: each section's heading, text and history line (the Acts that enacted and amended it). The annotations (Sentencing Commission Comments, Compiler's Notes, Amendments, Cross-References, Law Reviews, Attorney General Opinions, Notes to Decisions) are not.

## Dates

Each version is dated the day its release was issued: 2020-09-01 (release 72), 2020-09-30 (73), 2020-12-22 (74), 2021-02-04 (75) and 2021-05-21 (76). A release date is not the day the changes in it took effect, and the Acts behind each change are not credited, so every change after the first release is committed by the publisher as "unexplained". A release identical to the one before for a chapter is not a version.

## How it is checked

Every version is read back from git on the day it took effect and on the day before (`tools/check_repo.py`) and must match `corpus.json`; the results are in `REPRODUCE.md`.

## What "author" means

The author of a commit is the law that made the change, with an e-mail address that cannot exist (`<law key>@gov.tn.invalid`). In this first build no dated history is available, so every commit is credited to the publisher as "oldest version available". The committer is always Lexifina.

## Limits

This is a 2020-2021 record, not the Tennessee Code as it stands today. The Internet Archive holds no release after 2021-05-21, and the current Code is published by LexisNexis on a free-access site behind a click-through agreement, which this build does not use. Only the Constitution and Titles 39, 48 and 66 are included. Amendments after 2021-05-21 are missing.
