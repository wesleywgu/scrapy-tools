from GNews import GNews

if __name__ == '__main__':
  googlenews = GNews(period='w')
  googlenews.search('拼多多')
  print(googlenews.result())
