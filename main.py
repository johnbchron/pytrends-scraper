
from pytrends.request import TrendReq
from multiprocessing import Pool
import json, csv, requests, time, random, logging, sys, numpy as np, datetime

def setup_logging():
	logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)

	logging.basicConfig(format='[%(asctime)s][%(levelname)s][%(name)s]\t%(message)s',
											datefmt='%m/%d/%Y %H:%M:%S',
											handlers=[logging.StreamHandler(sys.stdout)],
											level=logging.INFO)

def check_trend(keyword):
	data = None
	while True:
		try:
			# options = []
			options = ['http://nicktb:nickspassword_country-us_lifetime-10s@geo.iproyal.com:22323' for x in range(100)]
			pytrends = TrendReq(hl='en-US', tz=360, proxies=options, retries=3, backoff_factor=0.5)

			cat = '0'
			timeframes = ['today 5-y', 'today 12-m', 'today 3-m', 'today 1-m']
			geo = ''
			gprop = ''
			pytrends.build_payload([keyword], cat, timeframes[0], geo, gprop)
			data = pytrends.interest_over_time()
		except requests.exceptions.ChunkedEncodingError as ex:
			logging.error("ChunkedEncodingError, retrying keyword \"%s\"...", keyword)
			# print("exception: " + str(ex))
			continue
		except requests.exceptions.ConnectTimeout as ex:
			logging.error("ConnectTimeout, retrying keyword \"%s\"...", keyword)
			# print("exception: " + str(ex))
			time.sleep(5)
			continue
		except requests.exceptions.ProxyError as ex:
			logging.error("ProxyError, retrying keyword \"%s\"...", keyword)
			# print("exception: " + str(ex))
			time.sleep(random.uniform(3, 6))
			continue
		except requests.exceptions.RetryError as ex:
			logging.error("MaxRetryError, retrying keyword \"%s\"...", keyword)
			# print("exception: " + str(ex))
			time.sleep(10)
			continue
		break

	#Last 5 Year Mean
	mean = round(data.mean(),2)
	
	try:
		#Last Year Mean
		avg = round((data[keyword])[-52:].mean(),2)
	except KeyError:
		logging.error("key \"%s\" was not returned by google trends", keyword)
		with open("data/manifest-" + datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d") + ".txt", "a") as outfile:
			outfile.write(keyword + "\n")
		return
	
	#1 Year Mean Compared to 5 Years Ago Mean
	trend = round(((avg/mean[keyword]) - 1) * 100,2)
	
	#First Year Mean (Mean In The First Year Starting 5 Years Ago)
	avg2 = round((data[keyword])[:52].mean(),2)
	
	#Establish Data
	latest = round((data[keyword])[-1:].mean(),2)
	first = round((data[keyword])[:1].mean(),2)
	if first == 0:
		growth = np.inf
	else:
		growth = round((((latest - first) / first) * 100),2)

	#Growth Ifs
	if latest < 1:
		latest = 1

	if first < 1:
		first = 1

	if growth > 100:
		logging.info("%s %s%%", keyword, str(growth))
		with open("data/output-" + datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d") + ".csv", "a") as outfile:
			writer = csv.writer(outfile)
			writer.writerow([keyword, str(growth) + "%"])
	with open("data/manifest-" + datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d") + ".txt", "a") as outfile:
		outfile.write(keyword + "\n")

def main():
	with open("data/keywords.json", "r") as infile:
		all_keywords = json.load(infile)

	already_scraped = []
	try:
		with open("data/manifest-" + datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d") + ".txt", "r") as infile:
			already_scraped = infile.read().splitlines()
	except FileNotFoundError:
		pass

	keywords = [x for x in all_keywords if x not in already_scraped]

	with open("data/output-" + datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d") + ".csv", "w") as outfile:
		writer = csv.writer(outfile)
		writer.writerow(["keyword", "growth"])

	if len(already_scraped) == len(all_keywords):
		logging.info("all keywords have already been scraped")
		return

	with Pool(40) as p:
		p.map(check_trend, keywords)

if __name__ == "__main__":
	setup_logging()
	main()