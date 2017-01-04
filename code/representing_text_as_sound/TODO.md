- is phonetic alphabet a better representation for text understanding?
- reduces dimensionality compared to characters
- stemming is implied by shared phonetics


### practicalities
- network for ingesting hybrid input
  - perf on characters
  - perf on hybrid characters only
  - perf on hybrid input

- get raw text
  - function to go from raw text to representation
    - tokenizer
    - spaces between alphabetic words

- dict improvements
  - add numbers [spell out]
  - add years [spell out]
  - add alphabetic words []
  - add accented words
  - tokenization (apostrophes, hyphens, abbreviations)
  - odd tokens [br]
