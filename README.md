# How it works

1. Downloads data from the ATP (`Playwright`)
2. Generates graphs (`matplotlib`)
3. Fills `.html` templates (`Jinja2`)
4. Renders images (`Playwright`)

# Installation

1. `pip install -r requirements.txt`
2. Setup [Playwright](https://playwright.dev/), especially `PLAYWRIGHT_BROWSERS_PATH`
3. `python3 .`

# Result

![1_ranking](output/1_ranking.png)
![2_game_set_match](output/2_game_set_match.png)
![3_game_set_match_2](output/3_game_set_match_2.png)
![4_map](output/4_map.png)
![5_body](output/5_body.png)
![6_income](output/6_income.png)
![7_fin](output/7_fin.png)
