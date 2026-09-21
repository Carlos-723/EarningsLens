# Real report fixtures

These UTF-8 text fixtures were extracted with `pypdf` from five public 2025 Q1
reports published by the Shenzhen Stock Exchange. Keeping text instead of binary
PDFs makes the regression suite small and deterministic.

- 000001 Ping An Bank
- 000900 Modern Investment
- 002555 37 Interactive Entertainment
- 002594 BYD
- 300750 CATL

The tests verify the reported revenue, attributable net profit, operating cash
flow, units, year-on-year changes, source section, and page number.
