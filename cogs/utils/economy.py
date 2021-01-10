from bs4 import BeautifulSoup
import aiohttp


async def stockgrab(url):
    headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as page:
            soup = BeautifulSoup(await page.text(),  'html.parser')
    stockdata = []
    table = soup.find('table', attrs={'class': 'W(100%)'})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        stockdata.append([ele for ele in cols if ele])
    return stockdata
