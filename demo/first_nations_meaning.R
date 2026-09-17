################ INSTALLS ###################
required_packages <- c(
  "DBI",
  "RPostgres",
  "tidyverse",
  "remotes",
  "tidytext",
  "lexicon",
  "quanteda",
  "textclean",
  "textshape"
)

to_install <- setdiff(required_packages, rownames(installed.packages()))
if (length(to_install)) {
  install.packages(to_install, repos = "https://cloud.r-project.org")
}

library(DBI)
library(tidyverse)
library(remotes)
library(stringr)
library(tidytext)

if (!"textstem" %in% rownames(installed.packages())) {
  remotes::install_github(
    "trinker/textstem",
    dependencies = TRUE,
    upgrade = "never"
  )
}

################ READ FROM DB ###################
con <- dbConnect(
  RPostgres::Postgres(),
  dbname = "prisma_db",
  host = "localhost",
  port = 5432,
  user = "prisma_user",
  password = "prisma_password"
)

query <- "
SELECT
    d.id AS document_id,
    ((EXTRACT(YEAR FROM sd.date)::int / 10) * 10) AS decade,
    sd.date,
    d.text
FROM \"SittingDay\" sd
JOIN \"Document\" d
    ON d.\"sittingDayId\" = sd.id
WHERE
    lower(d.text) LIKE '%aboriginal%'
    OR lower(d.text) LIKE '%aborigine%'
    OR lower(d.text) LIKE '%indigenous%'
    OR lower(d.text) LIKE '%first nation%'
    OR lower(d.text) LIKE '%first nations%'
    OR lower(d.text) LIKE '%first people%'
    OR lower(d.text) LIKE '%first peoples%'
    OR lower(d.text) LIKE '%first australians%'
    OR lower(d.text) LIKE '%torres strait%'
    OR lower(d.text) LIKE '%torres strait islander%'
    OR lower(d.text) LIKE '%torres strait islanders%'
    OR lower(d.text) LIKE '%native%'
    OR lower(d.text) LIKE '%natives%'
    OR lower(d.text) LIKE '%blackfellow%'
    OR lower(d.text) LIKE '%blackfellows%'
    OR lower(d.text) LIKE '%black fellow%'
    OR lower(d.text) LIKE '%black fellows%'
    OR lower(d.text) LIKE '%tribe%'
    OR lower(d.text) LIKE '%tribes%'
    OR lower(d.text) LIKE '%tribesman%'
    OR lower(d.text) LIKE '%tribesmen%'
    OR lower(d.text) LIKE '%tribeswoman%'
    OR lower(d.text) LIKE '%tribeswomen%'
    OR lower(d.text) LIKE '%tribal%'
    OR lower(d.text) LIKE '%half-caste%'
    OR lower(d.text) LIKE '%half caste%'
    OR lower(d.text) LIKE '%half-blood%'
    OR lower(d.text) LIKE '%half blood%'
    OR lower(d.text) LIKE '%full-blood%'
    OR lower(d.text) LIKE '%full blood%'
    OR lower(d.text) LIKE '%full-blooded%'
    OR lower(d.text) LIKE '%full blooded%'
    OR lower(d.text) LIKE '%quarter-caste%'
    OR lower(d.text) LIKE '%quarter caste%'
    OR lower(d.text) LIKE '%quarter-blood%'
    OR lower(d.text) LIKE '%quarter blood%'
    OR lower(d.text) LIKE '%quadroon%'
    OR lower(d.text) LIKE '%quadroons%'
    OR lower(d.text) LIKE '%octoroon%'
    OR lower(d.text) LIKE '%octoroons%'
ORDER BY sd.date;
"


results <- dbGetQuery(con, query)


################ DEFINE CLEANING FUNCTION ###################
clean_text <- function(text) {
  text <- tolower(text)

  text <- gsub("[-/]", " ", text)
  text <- gsub("[^[:alpha:][:space:]]", " ", text)

  tokens <- unlist(strsplit(text, "\\s+"), use.names = FALSE)
  tokens <- tokens[tokens != ""]

  tokens <- textstem::lemmatize_words(tokens)

  tokens
}

############ DEFINE ANCHOR SEQUENCES ###########

anchor_phrases <- c(
  "aboriginal",
  "aboriginals",
  "aborigine",
  "aborigines",
  "indigenous",
  "native aboriginal",
  "native aboriginals",
  "native aborigine",
  "native aborigines",
  "native indigenous",
  "first nation",
  "first nations",
  "first people",
  "first peoples",
  "torres strait",
  "torres strait islander",
  "torres strait islanders"
#   # "native",
#   # "natives",
#   # "blackfellow",
#   # "blackfellows",
#   # "black fellow",
#   # "black fellows",
#   # "tribe",
#   # "tribes",
#   # "tribesman",
#   # "tribesmen",
#   # "tribeswoman",
#   # "tribeswomen",
#   # "tribal",
#   "half-caste",
#   "half-castes",
#   "half caste",
#   "half castes",
#   "half-blood",
#   "half-bloods",
#   "half blood",
#   "half bloods",
#   "full-blood",
#   "full-bloods",
#   "full blood",
#   "full bloods",
#   "full-blooded",
#   "full blooded",
#   "quarter-caste",
#   "quarter-castes",
#   "quarter caste",
#   "quarter castes",
#   "quarter-blood",
#   "quarter-bloods",
#   "quarter blood",
#   "quarter bloods",
#   "quadroon",
#   "quadroons",
#   "octoroon",
#   "octoroons"
)


anchor_tokens <- lapply(anchor_phrases, clean_text)
anchor_tokens <- anchor_tokens[lengths(anchor_tokens) > 0]
anchor_tokens <- unique(anchor_tokens)

############## DEFINE EXTRACTION FUNCTION ###########

remove_anchor_sequences <- function(tokens, anchor_tokens) {
  n <- length(tokens)
  if (n == 0) {
    return(character(0))
  }

  output <- character(0)
  i <- 1

  while (i <= n) {
    found_matches <- list()

    for (j in seq_along(anchor_tokens)) {
      anchor <- anchor_tokens[[j]]
      k <- length(anchor)

      if (i + k - 1 <= n) {
        segment <- tokens[i:(i + k - 1)]
        if (identical(segment, anchor)) {
          found_matches[[length(found_matches) + 1]] <- list(
            anchor = anchor,
            length = k
          )
        }
      }
    }

    if (length(found_matches) > 0) {
      lengths <- sapply(found_matches, function(x) x$length)
      best_match <- found_matches[[which.max(lengths)]]
      i <- i + best_match$length
    } else {
      output <- c(output, tokens[i])
      i <- i + 1
    }
  }

  output
}

############## DEFINE EXTRACTION FUNCTION ###########
extract_windows <- function(tokens, anchor_tokens, window_n = 5) {
  matches <- list()
  match_id <- 1

  n <- length(tokens)
  if (n == 0) {
    return(NULL)
  }

  i <- 1
  while (i <= n) {
    found_matches <- list()

    for (j in seq_along(anchor_tokens)) {
      anchor <- anchor_tokens[[j]]
      k <- length(anchor)

      if (i + k - 1 <= n) {
        segment <- tokens[i:(i + k - 1)]

        if (identical(segment, anchor)) {
          found_matches[[length(found_matches) + 1]] <- list(
            anchor = anchor,
            length = k
          )
        }
      }
    }

    if (length(found_matches) > 0) {
      lengths <- sapply(found_matches, function(x) x$length)
      best_idx <- which.max(lengths)
      best_match <- found_matches[[best_idx]]

      k <- best_match$length
      start_w <- max(1, i - window_n)
      end_w <- min(n, i + k - 1 + window_n)

      left_tokens_raw <- if (start_w <= i - 1) tokens[start_w:(i - 1)] else character(0)
      right_tokens_raw <- if (i + k <= end_w) tokens[(i + k):end_w] else character(0)

      left_tokens <- remove_anchor_sequences(left_tokens_raw, anchor_tokens)
      right_tokens <- remove_anchor_sequences(right_tokens_raw, anchor_tokens)

      left_context <- paste(left_tokens, collapse = " ")
      right_context <- paste(right_tokens, collapse = " ")
      window_text <- paste(c(left_tokens, right_tokens), collapse = " ")

      matches[[match_id]] <- data.frame(
        anchor = paste(best_match$anchor, collapse = " "),
        anchor_start = i,
        anchor_end = i + k - 1,
        window_start = start_w,
        window_end = end_w,
        left_context = left_context,
        right_context = right_context,
        window_text = window_text,
        stringsAsFactors = FALSE
      )

      match_id <- match_id + 1
      i <- i + k
    } else {
      i <- i + 1
    }
  }

  if (length(matches) == 0) {
    return(NULL)
  }

  bind_rows(matches)
}

############## CLEAN RESULTS #########
library(parallel)

results$tokens <- mclapply(results$text, clean_text, mc.cores = 20)

########## EXTRACT THE WINDOWS #####
all_windows_list <- mclapply(
  seq_len(nrow(results)),
  function(i) {
    out <- extract_windows(results$tokens[[i]], anchor_tokens, window_n = 10)

    if (is.null(out)) {
      return(NULL)
    }

    out$document_id <- results$document_id[i]
    out$date <- results$date[i]
    out$decade <- results$decade[i]
    out
  },
  mc.cores = 20
)


all_windows_df <- bind_rows(all_windows_list)

# Various Governmental words to clean out
custom_stops <- c( "australia", "australian", "government", "minister", 'house', "department", "territory", "territories", "honorable", "honourable", "country", "affairs", "interjection", "senator", "commonwealth", "question", "questions", "notice", "bill", "act", "report", "committee", "provided", "time", "the", "of", "be", "to", "and", "that", "a", "in", "have", "i", "for", "not", "or", "as", "it", "from", "with", "by", "we", "who", "which", "new", "this", "they", "their", "any", "there", "do", "if", "on", "no", "would", "will", "but", "his", "he", "at", "should", "under", "much", "our", "can", "other", "man", "take", "bear",  "our", "much", "can", "one", "other", "some", "all", "about", "them",
  "take", "make", "good", "man", "s", "may", "so", "affair", "say", "state", "shall", "very", "out", "what", "why", "queensland", "non", "member", "mr", "my", "many", "year", "upon", "when", "south", "west","north", "east", "know", "only", "such")

words <- all_windows_df %>%
  group_by(decade) %>%
  summarise(
    top_words = list(
      window_text %>%
        str_to_lower() %>%
        str_split("\\s+") %>%
        unlist() %>%
        tibble(word = .) %>%
        filter(word != "") %>%
        filter(!word %in% custom_stops) %>%
        count(word, sort = TRUE) %>%
        slice_head(n = 10) %>%
        pull(word)
    ),
    .groups = "drop"
  ) %>%
  mutate(top_words = sapply(top_words, paste, collapse = ", "))

saveRDS(words, 'common_words.R')
