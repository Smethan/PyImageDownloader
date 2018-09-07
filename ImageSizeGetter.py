import aiohttp
import asyncio
import json
import argparse

class Scraper:
	def __init__(self, session):
		self.session = session

	@property
	def Header(self):
		return {
			'User-Agent': 'ImageGetter/1.0 (Yeet)'
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

	async def grab_json(self, **kwargs):

		async with self.session.get(self.baseURL + self.extension, params=kwargs, headers=self.Header) as resp:
			print(resp)
			if resp.status == 200:
				# print(await resp.json())
				return await resp.json()
			raise Exception(f"Could not get json from website! Maybe the URL is wrong? Response code: {resp.status()} ")

	async def find_size(self, limit=50, tags=''):
		before_id = None
		size = 0
		imgcount = 0
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
				id_list = [i["id"]]
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
		kilobytes = size/1024
		megabytes = kilobytes/1024
		
		return size, kilobytes, megabytes, imgcount
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

class Runner:
	
	def parse_arg(self):
		ap = argparse.ArgumentParser()
		ap.add_argument("-a", "--amount", help="how many images to check. Default: 50")
		ap.add_argument("-e9", "--e926", help="Search e926", action='store_true')
		ap.add_argument("-e6", "--e621", help="Search e621", action='store_true')
		ap.add_argument("-t", "--tags", nargs="+", help="tags to search")
		args = vars(ap.parse_args())
		return args
	async def main(self):
		async with aiohttp.ClientSession() as session:
			args = self.parse_arg()
			limit = 0
			if args["amount"] is not None:
				limit = int(args["amount"])
			else:
				limit = 50
			if args["tags"] is not None:
				tags = ' '.join(args["tags"])
			else:
				tags = ""
			if args["e926"] is not None:
				FinalBytes, FinalKilo, FinalMega, imgcount = await e926(session).find_size(limit=limit, tags=tags)
			elif args["e621"] is not None:
				FinalBytes, FinalKilo, FinalMega, imgcount = await e621(session).find_size(limit=limit, tags=tags)
			else:
				raise Exception("Invalid Input!")
			await session.close()
			print(f"Searched for {limit} images, found {imgcount} images, Bytes: {FinalBytes}, Kilobytes: {FinalKilo}, Megabytes: {FinalMega}")
if __name__ == "__main__":
	r = Runner()
	loop = asyncio.get_event_loop()
	task = loop.create_task(r.main())
	loop.run_until_complete(task)
