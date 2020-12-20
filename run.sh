mkdir -p taronews
python3 taro_crawler.py --out_dir TaroNews
mkdir -p TaipeiTimes
python3 tt_crawler.py --out_dir TaipeiTimes
mkdir -p PeopoNews
python3 peopo_crawler.py --out_dir PeopoNews
mkdir -p WealthNews
python3 wealth_crawler.py --out_dir WealthNews
