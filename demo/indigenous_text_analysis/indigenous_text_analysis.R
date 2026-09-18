################ PACKAGES ################
required_packages <- c(
  "DBI",
  "RPostgres",
  "tidyverse",
  "remotes"
)

to_install <- setdiff(required_packages, rownames(installed.packages()))
if (length(to_install)) {
  install.packages(to_install, repos = "https://cloud.r-project.org")
}

library(DBI)
library(tidyverse)
library(remotes)
library(stringr)
library(textstem)

if (!"textstem" %in% rownames(installed.packages())) {
  remotes::install_github(
    "trinker/textstem",
    dependencies = TRUE,
    upgrade = "never"
  )
}

################ TEXT NORMALISATION ################
# This creates a search representation only. The original Hansard text is retained.
clean_text <- function(text) {
  text <- str_to_lower(text)
  text <- str_replace_all(text, "[[:dash:]/]", " ")
  text <- str_replace_all(text, "[^[:alpha:][:space:]]", " ")
  text <- str_squish(text)

  if (is.na(text) || text == "") {
    return(character(0))
  }

  tokens <- str_split(text, "\\s+", simplify = FALSE)[[1]]
  textstem::lemmatize_words(tokens)
}

################ INDIGENOUS-REFERENCE LEXICON ################
# The lexicon is intentionally a retrieval device, not a list of recommended
# contemporary expressions. Historical and offensive source-language terms are
# included because otherwise relevant older debates would be systematically missed.
#
# Construction:
#   1. contemporary collective expressions;
#   2. terminology appearing in historical administrative and classificatory usage;
#   3. historical labels documented in Indigenous Australian studies literature; and
#   4. a small, illustrative set of regional, nation and language identities.
#
# The regional list is not exhaustive. A full implementation should import preferred
# names and spelling variants from AIATSIS AUSTLANG and retain its stable identifiers.

term_lexicon <- tribble(
  ~phrase,                    ~category,                     ~confidence, ~historical_offensive,
  "aboriginal",              "collective_identity",        "high",      FALSE,
  "aboriginals",             "collective_identity",        "high",      TRUE,
  "aborigine",               "collective_identity",        "high",      TRUE,
  "aborigines",              "collective_identity",        "high",      TRUE,
  "indigenous",              "collective_identity",        "medium",    FALSE,
  "first nation",            "collective_identity",        "medium",    FALSE,
  "first nations",           "collective_identity",        "medium",    FALSE,
  "first people",            "collective_identity",        "medium",    FALSE,
  "first peoples",           "collective_identity",        "medium",    FALSE,
  "first australian",        "collective_identity",        "medium",    FALSE,
  "first australians",       "collective_identity",        "medium",    FALSE,
  "torres strait islander",  "collective_identity",        "high",      FALSE,
  "torres strait islanders", "collective_identity",        "high",      FALSE,
  "torres strait",           "geographic_context",         "low",       FALSE,
  "aboriginal native",       "historical_collective",      "high",      TRUE,
  "aboriginal natives",      "historical_collective",      "high",      TRUE,
  "native aboriginal",       "historical_collective",      "high",      TRUE,
  "native aboriginals",      "historical_collective",      "high",      TRUE,
  "australian native",       "historical_collective",      "medium",    TRUE,
  "australian natives",      "historical_collective",      "medium",    TRUE,
  "aboriginal inhabitant",   "historical_collective",      "high",      TRUE,
  "aboriginal inhabitants",  "historical_collective",      "high",      TRUE,
  "native inhabitant",       "historical_collective",      "low",       TRUE,
  "native inhabitants",      "historical_collective",      "low",       TRUE,
  "aboriginal race",         "historical_collective",      "high",      TRUE,
  "native race",             "historical_collective",      "low",       TRUE,
  "australian black",        "historical_collective",      "medium",    TRUE,
  "australian blacks",       "historical_collective",      "medium",    TRUE,
  "aboriginal descent",      "historical_classification",  "high",      FALSE,
  "aboriginal origin",       "historical_classification",  "high",      FALSE,
  "aboriginal blood",        "historical_classification",  "high",      TRUE,
  "part aboriginal",         "historical_classification",  "high",      TRUE,
  "mixed descent",           "historical_classification",  "medium",    TRUE,
  "mixed blood",             "historical_classification",  "medium",    TRUE,
  "half caste",              "historical_classification",  "high",      TRUE,
  "half castes",             "historical_classification",  "high",      TRUE,
  "half blood",              "historical_classification",  "high",      TRUE,
  "full blood",              "historical_classification",  "high",      TRUE,
  "full blooded",            "historical_classification",  "high",      TRUE,
  "quarter caste",           "historical_classification",  "high",      TRUE,
  "quarter blood",           "historical_classification",  "high",      TRUE,
  "three quarter caste",     "historical_classification",  "high",      TRUE,
  "quadroon",                "historical_classification",  "high",      TRUE,
  "quadroons",               "historical_classification",  "high",      TRUE,
  "octoroon",                "historical_classification",  "high",      TRUE,
  "octoroons",               "historical_classification",  "high",      TRUE,
  "mulatto",                 "historical_classification",  "medium",    TRUE,
  "detribalised",            "historical_classification",  "medium",    TRUE,
  "detribalized",            "historical_classification",  "medium",    TRUE,
  "semi detribalised",       "historical_classification",  "medium",    TRUE,
  "semi detribalized",       "historical_classification",  "medium",    TRUE,
  "blackfellow",             "historical_label",           "high",      TRUE,
  "blackfellows",            "historical_label",           "high",      TRUE,
  "black fellow",            "historical_label",           "high",      TRUE,
  "black fellows",           "historical_label",           "high",      TRUE,
  "blackfella",              "historical_or_community",    "medium",    FALSE,
  "blackfellas",             "historical_or_community",    "medium",    FALSE,
  "blackfulla",              "historical_or_community",    "medium",    FALSE,
  "blackfullas",             "historical_or_community",    "medium",    FALSE,
  "myall",                   "historical_label",           "medium",    TRUE,
  "myalls",                  "historical_label",           "medium",    TRUE,
  "lubra",                   "historical_label",           "medium",    TRUE,
  "lubras",                  "historical_label",           "medium",    TRUE,
  "gin",                     "ambiguous_historical_label", "low",       TRUE,
  "gins",                    "ambiguous_historical_label", "low",       TRUE,
  "piccaninny",              "historical_label",           "medium",    TRUE,
  "piccaninnies",            "historical_label",           "medium",    TRUE,
  "picaninny",               "historical_label",           "medium",    TRUE,
  "picaninnies",             "historical_label",           "medium",    TRUE,
  "darkie",                  "ambiguous_historical_label", "low",       TRUE,
  "darkies",                 "ambiguous_historical_label", "low",       TRUE,
  "native",                  "ambiguous_collective",       "low",       TRUE,
  "natives",                 "ambiguous_collective",       "low",       TRUE,
  "black",                   "ambiguous_collective",       "low",       TRUE,
  "blacks",                  "ambiguous_collective",       "low",       TRUE,
  "tribe",                   "ambiguous_collective",       "low",       TRUE,
  "tribes",                  "ambiguous_collective",       "low",       TRUE,
  "tribal",                  "ambiguous_collective",       "low",       TRUE,
  "koori",                   "regional_or_group_identity", "high",      FALSE,
  "koorie",                  "regional_or_group_identity", "high",      FALSE,
  "murri",                   "regional_or_group_identity", "high",      FALSE,
  "murrie",                  "regional_or_group_identity", "high",      FALSE,
  "nunga",                   "regional_or_group_identity", "high",      FALSE,
  "noongar",                 "regional_or_group_identity", "high",      FALSE,
  "nyungar",                 "regional_or_group_identity", "high",      FALSE,
  "nyoongar",                "regional_or_group_identity", "high",      FALSE,
  "palawa",                  "regional_or_group_identity", "high",      FALSE,
  "anangu",                  "regional_or_group_identity", "high",      FALSE,
  "yolngu",                  "regional_or_group_identity", "high",      FALSE,
  "wiradjuri",               "regional_or_group_identity", "high",      FALSE,
  "ngunnawal",               "regional_or_group_identity", "high",      FALSE,
  "ngambri",                 "regional_or_group_identity", "high",      FALSE,
  "gadigal",                 "regional_or_group_identity", "high",      FALSE,
  "eora",                    "regional_or_group_identity", "high",      FALSE,
  "meriam",                  "regional_or_group_identity", "high",      FALSE,
  "kaurareg",                "regional_or_group_identity", "high",      FALSE,
  "zenadth kes",             "regional_or_group_identity", "high",      FALSE
)

################ READ FROM DATABASE ################
con <- dbConnect(
  RPostgres::Postgres(),
  dbname = Sys.getenv("HANSARD_DB_NAME", "prisma_db"),
  host = Sys.getenv("HANSARD_DB_HOST", "localhost"),
  port = as.integer(Sys.getenv("HANSARD_DB_PORT", "5432")),
  user = Sys.getenv("HANSARD_DB_USER", "prisma_user"),
  password = Sys.getenv("HANSARD_DB_PASSWORD", "prisma_password")
)

# Use the same lexicon for database prefiltering and subsequent window extraction.
# PostgreSQL word-boundary constraints avoid substring matches such as "gin" inside
# an unrelated longer word. Spaces, hyphens, slashes and line breaks are treated as
# interchangeable separators to accommodate historical typography and OCR.
sql_terms <- term_lexicon$phrase %>%
  str_to_lower() %>%
  str_replace_all("[[:dash:]/]", " ") %>%
  str_squish() %>%
  unique() %>%
  str_replace_all(" ", "[[:space:]/-]+")

sql_regex <- paste0(
  "[[:<:]](",
  paste(sql_terms, collapse = "|"),
  ")[[:>:]]"
)

query <- paste0(
  "SELECT\n",
  "    d.id AS document_id,\n",
  "    ((EXTRACT(YEAR FROM sd.date)::int / 10) * 10) AS decade,\n",
  "    sd.date,\n",
  "    d.text\n",
  "FROM \"SittingDay\" sd\n",
  "JOIN \"Document\" d ON d.\"sittingDayId\" = sd.id\n",
  "WHERE d.text ~* ", as.character(dbQuoteString(con, sql_regex)), "\n",
  "ORDER BY sd.date;"
)

results <- dbGetQuery(con, query)
dbDisconnect(con)

if (nrow(results) == 0) {
  stop("No documents matched the Indigenous-reference lexicon.")
}

################ PREPARE ANCHOR SEQUENCES ################
# Lemmatization can collapse variants (for example, singular and plural). Preserve
# all source phrases and categories associated with each cleaned anchor.
anchor_lookup <- term_lexicon %>%
  mutate(
    anchor_tokens = map(phrase, clean_text),
    anchor = map_chr(anchor_tokens, ~ paste(.x, collapse = " "))
  ) %>%
  filter(anchor != "") %>%
  group_by(anchor) %>%
  summarise(
    lexicon_phrases = paste(unique(phrase), collapse = " | "),
    categories = paste(unique(category), collapse = " | "),
    confidence = paste(unique(confidence), collapse = " | "),
    historical_offensive = any(historical_offensive),
    .groups = "drop"
  )

anchor_tokens <- str_split(anchor_lookup$anchor, "\\s+")

################ WINDOW EXTRACTION ################
remove_anchor_sequences <- function(tokens, anchor_tokens) {
  n <- length(tokens)
  if (n == 0) {
    return(character(0))
  }

  output <- character(0)
  i <- 1

  while (i <= n) {
    matching_lengths <- integer(0)

    for (anchor in anchor_tokens) {
      k <- length(anchor)
      if (i + k - 1 <= n && identical(tokens[i:(i + k - 1)], anchor)) {
        matching_lengths <- c(matching_lengths, k)
      }
    }

    if (length(matching_lengths)) {
      i <- i + max(matching_lengths)
    } else {
      output <- c(output, tokens[i])
      i <- i + 1
    }
  }

  output
}

extract_windows <- function(tokens, anchor_tokens, window_n = 10) {
  matches <- list()
  match_id <- 1
  n <- length(tokens)

  if (n == 0) {
    return(NULL)
  }

  i <- 1
  while (i <= n) {
    found_matches <- list()

    for (anchor in anchor_tokens) {
      k <- length(anchor)
      if (i + k - 1 <= n && identical(tokens[i:(i + k - 1)], anchor)) {
        found_matches[[length(found_matches) + 1]] <- list(
          anchor = anchor,
          length = k
        )
      }
    }

    if (length(found_matches)) {
      lengths <- map_int(found_matches, "length")
      best_match <- found_matches[[which.max(lengths)]]
      k <- best_match$length

      start_w <- max(1, i - window_n)
      end_w <- min(n, i + k - 1 + window_n)

      left_raw <- if (start_w <= i - 1) tokens[start_w:(i - 1)] else character(0)
      right_raw <- if (i + k <= end_w) tokens[(i + k):end_w] else character(0)

      left_tokens <- remove_anchor_sequences(left_raw, anchor_tokens)
      right_tokens <- remove_anchor_sequences(right_raw, anchor_tokens)

      matches[[match_id]] <- tibble(
        anchor = paste(best_match$anchor, collapse = " "),
        anchor_start = i,
        anchor_end = i + k - 1,
        window_start = start_w,
        window_end = end_w,
        left_context = paste(left_tokens, collapse = " "),
        right_context = paste(right_tokens, collapse = " "),
        window_text = paste(c(left_tokens, right_tokens), collapse = " ")
      )

      match_id <- match_id + 1
      i <- i + k
    } else {
      i <- i + 1
    }
  }

  if (!length(matches)) {
    return(NULL)
  }

  bind_rows(matches)
}

################ CLEAN AND EXTRACT ################
library(parallel)

available_cores <- parallel::detectCores(logical = FALSE)
N_CORES <- if (.Platform$OS.type == "windows") {
  1L
} else {
  max(1L, min(20L, available_cores - 1L))
}

results$tokens <- mclapply(results$text, clean_text, mc.cores = N_CORES)

all_windows_list <- mclapply(
  seq_len(nrow(results)),
  function(i) {
    out <- extract_windows(results$tokens[[i]], anchor_tokens, window_n = 10)

    if (is.null(out)) {
      return(NULL)
    }

    out %>%
      mutate(
        document_id = results$document_id[i],
        date = results$date[i],
        decade = results$decade[i]
      )
  },
  mc.cores = N_CORES
)

all_windows_df <- bind_rows(all_windows_list) %>%
  left_join(anchor_lookup, by = "anchor") %>%
  arrange(date, document_id, anchor_start)

if (nrow(all_windows_df) == 0) {
  stop("Documents were retrieved, but no token-level anchors were found.")
}

# Retain the complete matched-window data for audit and validation. In particular,
# low-confidence terms such as native, tribe, black and gin should be inspected in
# context rather than treated automatically as references to First Nations peoples.
saveRDS(all_windows_df, "indigenous_term_windows.rds")

################ DECADE-LEVEL CONTEXT WORDS ################
custom_stops <- c(
  "australia", "australian", "government", "minister", "house", "department",
  "territory", "territories", "honorable", "honourable", "country", "affairs",
  "interjection", "senator", "commonwealth", "question", "questions", "notice",
  "bill", "act", "report", "committee", "provided", "time", "the", "of", "be",
  "to", "and", "that", "a", "in", "have", "i", "for", "not", "or", "as",
  "it", "from", "with", "by", "we", "who", "which", "new", "this", "they",
  "their", "any", "there", "do", "if", "on", "no", "would", "will", "but",
  "his", "he", "at", "should", "under", "much", "our", "can", "other", "man",
  "take", "bear", "one", "some", "all", "about", "them", "make", "good", "s",
  "may", "so", "affair", "say", "state", "shall", "very", "out", "what", "why",
  "queensland", "non", "member", "mr", "my", "many", "year", "upon", "when",
  "south", "west", "north", "east", "know", "only", "such"
)

words <- all_windows_df %>%
  group_by(decade) %>%
  summarise(
    top_words = list(
      window_text %>%
        str_to_lower() %>%
        str_split("\\s+") %>%
        unlist() %>%
        tibble(word = .) %>%
        filter(word != "", !word %in% custom_stops) %>%
        count(word, sort = TRUE) %>%
        slice_head(n = 10) %>%
        pull(word)
    ),
    .groups = "drop"
  ) %>%
  mutate(top_words = map_chr(top_words, ~ paste(.x, collapse = ", ")))

saveRDS(words, "common_words.R")
