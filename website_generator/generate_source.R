library(magrittr)

repo_path <- ".."

#### nassa input ####

nassa_yml_paths <- list.files(
  path = repo_path,
  pattern = "NASSA.yml",
  recursive = T,
  full.names = T  
)

nassa_table <- purrr::map_dfr(
  nassa_yml_paths,
  function(nassa_yml_path) {
    nassa_yml <- yaml::read_yaml(nassa_yml_path)
    tibble::tibble(
      path = basename(dirname(nassa_yml_path)),
      id = nassa_yml$id,
      title = nassa_yml$title,
      moduleVersion = nassa_yml$moduleVersion,
      `View` = paste0("[View](", path, ".html)"),
    )
  }
)

#### prepare package-wise .Rmd files ####

generate_Rmd <- function(x) {
  out_path <- file.path("website_source", paste0(x, ".Rmd"))
  template <- readLines("package_page_template.Rmd")
  template_mod <- gsub("####module_name####", x, template)
  writeLines(template_mod, con = out_path)
}
purrr::walk(nassa_table$path, generate_Rmd)

#### create index.Rmd file ####

write(c(
  "---",
  "title: NASSA modules",
  "---",
  "",
  knitr::kable(nassa_table, format = "pipe") %>% as.character()
  ),
  file = file.path("website_source", "index.Rmd")
)

#### render website from .Rmd files

rmarkdown::render_site(input = "website_source")
