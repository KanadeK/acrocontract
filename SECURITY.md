# Security policy

## Supported version

Security fixes are provided for the latest GitHub Release.

## Reporting

Please use GitHub's private vulnerability reporting for this repository. Do not attach sensitive
PDFs, production values, credentials, or personal data to a public issue. A minimal synthetic PDF
that reproduces the parser behavior is preferred.

## Boundaries

AcroContract reads local files only. It does not fetch URLs, upload PDFs, execute embedded PDF
JavaScript, or log form values in reports. `fill-test` writes to a distinct output path and rejects
encrypted, XFA, duplicate-name, and detached-widget surfaces instead of guessing.

PDF parsing is still processing untrusted input. Run the tool with ordinary user permissions and do
not point output paths at valuable files.
