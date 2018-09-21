import aiohttp
import asyncio
import json
import argparse
import uuid
import concurrent.futures as fut
import os
import threading
from termcolor import cprint
from progress.bar import Bar
from multiprocessing import Process
import time
loop = asyncio.new_event_loop()
class Scraper:
	def __init__(self, session):
		self.session = session

	@property
	def Header(self):
		return {
			'User-Agent': 'ImageGetter/1.0 (Made by electric_espeon)'
		}

	@property
	def baseURL(self):
		return None

	@property
	def extension(self):
		return None

	@property
	def fileSizePropName(self):
		return None

	@property
	def file_url(self):
		return None
	
	async def grab_json(self, **kwargs):

		async with self.session.get(self.baseURL + self.extension, params=kwargs, headers=self.Header) as resp:
			# print(resp)
			if resp.status == 200:
				# print(await resp.json())
				return await resp.json()
			raise Exception(f"Could not get json from website! Maybe the URL is wrong? Response code: {resp.status()} ")

	async def find_size(self, limit=50, tags=''):
		before_id = None
		size = 0
		imgcount = 0
		file_url_list = []
		id_list = []
		while limit > 320:
			limit1 = limit - 320
			limit = 320
			# print(tags)
			if before_id:
				json = await self.grab_json(limit=limit, before_id=before_id, tags=tags)
			else:
				json = await self.grab_json(limit=limit, tags=tags)
			if len(json) < 320:
				break
			for i in json:
				filesize = i[self.fileSizePropName] if i is not None else i
				size += filesize
				id_list.append(i["id"])
				file_url_list.append(i[self.file_url])
			before_id = id_list[len(id_list) - 1]
			limit = limit1
			imgcount += len(json)
		if before_id:
			json = await self.grab_json(limit=limit, before_id=before_id, tags=tags)
		else:
			json = await self.grab_json(limit=limit, tags=tags)
		imgcount += len(json)
		for i in json:
			filesize = i[self.fileSizePropName] if i is not None else i
			size += filesize
			file_url_list.append(i[self.file_url])
		kilobytes = size/1024
		megabytes = kilobytes/1024
		
		return size, kilobytes, megabytes, imgcount, file_url_list

	def thread_write(self, file, path):
		with open(path, "wb") as f:
			f.write(file)
	async def fetch(self, url):
		async with aiohttp.ClientSession() as r:
			response = await r.get(url, headers=self.Header)
			return await response.read()

	async def download(self, urls = [], tags="notag"):
		async with aiohttp.ClientSession() as session:
			with fut.ThreadPoolExecutor(max_workers=10000) as e:
				# print(urls)
				loop = asyncio.get_event_loop()
				
				asyncio.set_event_loop(loop)
				cprint("PID: " + str(os.getpid()), 'red')
				cprint("Started: " + str(time.time()), 'yellow')
				futures = []
				requests = []
				filenames = []
				bar = Bar("Downloading", max=len(urls))
				if not os.path.exists(tags):
					os.makedirs(tags)
				for i in urls:
					file_name, file_extension = os.path.splitext(i)
					othername = file_name.split("/")
					filename = othername[len(othername) - 1] + file_extension
					filenames.append(filename)
					if os.path.exists(os.path.join(tags, filename)):
						cprint("\r\x1b[K"+filename + " already exists, moving on...", 'red')
						bar.next()
						pass
					else:
						# if file_extension == ".png":
						# 	cprint("\r\x1b[K"+filename, 'green')
						# elif file_extension == ".jpg":
						# 	cprint("\r\x1b[K"+filename, 'yellow')
						# elif file_extension == ".gif":
						# 	cprint("\r\x1b[K"+filename, 'cyan')
						# elif file_extension == ".webm":
						# 	cprint("\r\x1b[K"+filename, 'magenta')
						# else:
						# 	cprint("\r\x1b[K"+filename, 'blue')
						# print(threading.active_count())
						requests.append(asyncio.ensure_future(self.fetch(i), loop=loop))
						
						
						
						
					
				# otherloop = asyncio.new_event_loop()
				# asyncio.set_event_loop(otherloop)
				cprint("Gathering urls...", 'blue')
				responses = asyncio.gather(*requests, loop=loop)
				cprint("Done", 'green')
				e = 0
				for i in await responses:
					
					filename = filenames[e]
					path = os.path.join(tags, filename)
					
					p = Process(target = self.thread_write, args=(i, path))
					futures.append(p)
					e = e+1
				# bar.next()
				for p in futures:
					p.start()
				cprint("Threads started: " + str(threading.active_count()), 'blue')
				for p in futures:
					p.join()
					bar.next()
				cprint("\nDone! Files saved to: " + os.getcwd() + "/" + tags, 'green')
				bar.finish()
class e926(Scraper):
	"""docstring for e926"""
	
	@property
	def baseURL(self):
		return "https://e926.net"

	@property
	def extension(self):
		return "/post/index.json"

	@property
	def fileSizePropName(self):
		return "file_size"
	@property
	def file_url(self):
		return "file_url"
	
class e621(Scraper):
	"""docstring for e926"""
	
	@property
	def baseURL(self):
		return "https://e621.net"

	@property
	def extension(self):
		return "/post/index.json"

	@property
	def fileSizePropName(self):
		return "file_size"

	@property
	def file_url(self):
		return "file_url"

class lb(Scraper):
	"""docstring for e926"""
	
	@property
	def baseURL(self):
		return "https://lolibooru.moe"

	@property
	def extension(self):
		return "/post/index.json"

	@property
	def fileSizePropName(self):
		return "file_size"

	@property
	def file_url(self):
		return "file_url"


class Runner:
	
	def parse_arg(self):
		ap = argparse.ArgumentParser()
		ap.add_argument("-a", "--amount", help="how many images to check. Default: 50")
		ap.add_argument("-e9", "--e926", help="Search e926", action='store_true')
		ap.add_argument("-e6", "--e621", help="Search e621", action='store_true')
		ap.add_argument("-lo", "--lb", help="search", action='store_true')
		ap.add_argument("-t", "--tags", nargs="+", help="tags to search")
		args = vars(ap.parse_args())
		return args
	async def main(self):
		async with aiohttp.ClientSession() as session:
			args = self.parse_arg()
			limit = 0
			fileList = []
			if args["amount"] is not None:
				limit = int(args["amount"])
			else:
				limit = 50
			if args["tags"] is not None:
				tags = ' '.join(args["tags"])
			else:
				tags = ""
			if args["e926"] is not False:
				FinalBytes, FinalKilo, FinalMega, imgcount, fileList = await e926(session).find_size(limit=limit, tags=tags)
			elif args["e621"] is not False:
				FinalBytes, FinalKilo, FinalMega, imgcount, fileList = await e621(session).find_size(limit=limit, tags=tags)
			elif args["lb"] is not False:
				FinalBytes, FinalKilo, FinalMega, imgcount, fileList = await lb(session).find_size(limit=limit, tags=tags)
			else:
				raise Exception("Invalid Input!")
			await session.close()
			input(f"Searched for {limit} images, found {imgcount} images, Bytes: {FinalBytes}, Kilobytes: {FinalKilo}, Megabytes: {FinalMega}\nPress any key to download, Ctrl+C to abort")
			loop = asyncio.get_running_loop()
			if args["tags"] is not None:
				await e621(session).download(fileList, tags=args["tags"][0])
			else:
				await e621(session).download(fileList)
			
if __name__ == "__main__":
	r = Runner()
	loop = asyncio.get_event_loop()
	task = loop.create_task(r.main())
	loop.run_until_complete(task)
