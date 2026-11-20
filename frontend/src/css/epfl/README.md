# EPFL design tokens

`tokens/` is copied unchanged from the `epfl-design` skill, version 0.3.0
(<https://github.com/EPFL-ENAC/epfl-design-skill>). It is the only place raw
colours, sizes and the font stack live. Everything else in the app uses
`var(--…)`.

Do not edit these files. To update, copy `tokens/` again from a newer version of
the skill.

Suisse Int'l loads from `enac-it-fonts.epfl.ch`, which serves `*.epfl.ch` sites
only. Anywhere else the text renders in Arial, the sanctioned fallback. Never add
font files to this project.
