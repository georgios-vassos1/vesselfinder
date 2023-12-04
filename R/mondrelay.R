# Install and load the required packages
library(httr)
library(rlist)
library(data.table)

consrtuct_query <- function(params) {
  paste0(names(params), "=", params, collapse = "&")
}

consrtuct_cookie_header <- function(cookies) {
  if (!is.null(cookies)) paste0(names(cookies), "=", cookies, collapse = "; ")
}

get_url <- function(base_url, params) {
  # Construct the query
  query <- consrtuct_query(params)
  # Construct the URL
  paste0(base_url, '?', query)
}

get_cookies <- function(ref_url, ...) {
  # Make the HTTP request
  post_ <- httr::POST(ref_url)
  
  # Check if the status code is 200
  if (httr::status_code(post_) == 200L) {
    # Extract cookies
    cookies <- httr::cookies(post_) |>
      # dplyr::select(name, value) |>
      (\(x) { setNames(as.list(x$value), x$name) })()
    
    return(cookies)
  }
}

get_verification_token <- function(ref_url, ...) {
  # Make the HTTP request
  get_ <- httr::GET(ref_url)

  # Check if the status code is 200
  if (httr::status_code(get_) == 200L) {

    # Extract the __RequestVerificationToken using regular expressions
    pattern <- 'token="([^"]+)"'
    token   <- stringr::str_match(httr::content(get_, "text"), pattern)[,2L]

    return(token)
  }
}

make_headers <- function(ref_url, token, cookies=NULL, ...) {
  c(
    "Accept"     = "application/json, text/plain, */*",
    "User-Agent" = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Cookie"     = consrtuct_cookie_header(cookies),
    "Referer"    = ref_url,
    "Requestverificationtoken" = token
  )
}

scrape_data <- function(base_url, params, headers, ...) {
  # Construct the URL
  url <- get_url(base_url, params)

  # Make the HTTP request
  response <- httr::GET(url, httr::add_headers(headers))

  # Check if the request was successful (status code 200)
  if (httr::status_code(response) == 200L) {
    # Parse the JSON content of the response
    return(httr::content(response, "parsed"))
  } else {
    cat("Request failed with status code", httr::status_code(response), "\n")
    cat("Response content:\n")
    cat(httr::content(response, "text"), "\n")
  }
}

conv2dt_ <- function(item) {
  cbind(
    data.table::as.data.table(item[c(1L,2L,7L,8L)]),
    data.table::as.data.table(rlist::list.flatten(item$Adresse)),
    data.table::as.data.table(rlist::list.flatten(item$Services)),
    data.table::as.data.table(rlist::list.flatten(item$Conges)),
    data.table::rbindlist(lapply(item$Horaires, data.table::as.data.table), fill=TRUE)
  )
}

conv2dt <- function(list_, fill = TRUE) {
  data.table::rbindlist(lapply(list_, conv2dt_), fill = fill)
}

## DEMO
# Reference Base URL
ref_base_url <- "https://www.mondialrelay.fr/trouver-le-point-relais-le-plus-proche-de-chez-moi/"

# Set the parameters
ref_params <- list(
  'codePays'   = 'ES',
  'codePostal' = '08023'
)

# Obtain the assets
ref_url <- get_url(ref_base_url, ref_params)
# cookies <- get_cookies(ref_url)
token   <- get_verification_token(ref_url)

# Target Base URL
base_url <- "https://www.mondialrelay.fr/api/parcelshop"

# Set the parameters
params <- list(
  'country'        = 'ES',
  'postcode'       = '08023',
  'city'           = '',
  'services'       = '',
  'excludeSat'     = 'false',
  'naturesAllowed' = '1,A,E,F,D,J,T,S,C',
  'agencesAllowed' = ''
)

headers <- make_headers(ref_url, token)
result  <- scrape_data(base_url, params, headers)

dt <- conv2dt(result)
