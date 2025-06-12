import struct

SECTOR_SIZE = 512
FILENAME_SIZE = 32
ENTRY_SIZE = FILENAME_SIZE+4+4

class GLFSImage:
	def __init__(self, path):
		self.file = path
		self.file = open(path, 'r+b')
	
	@classmethod
	def create(cls, path, total_sectors=2048):
		with open(path, 'wb') as f:
			superblock = b'GLFSv0\n' + b'\x00' * (SECTOR_SIZE - 7)
			f.write(superblock)
			
			dir_sector = b'\x00' * (SECTOR_SIZE - 8) + b'__END__\n'
			f.write(dir_sector)
			
			remaining_sectors = total_sectors - 2
			f.write(b'\x00' * remaining_sectors * SECTOR_SIZE)
		
	def read_sector(self, sector_num):
		self.file.seek(sector_num * SECTOR_SIZE)
		return self.file.read(SECTOR_SIZE)
		
	def write_sector(self, sector_num, data):
		if len(data) > SECTOR_SIZE:
			raise ValueError("Data exceeds sector size!")
		self.file.seek(sector_num * SECTOR_SIZE)
		self.file.write(data.ljust(SECTOR_SIZE, b'\x00'))
	
	def close(self):
		self.file.close()
		
	def check_superblock(self):
		self.file.seek(0)
		magic = self.file.read(7)
		return magic == b'GLFSv0\n'
		
	def parse_directory_table(self):
		buf = b''
		entries = []
		sector_num = 1
		
		while True:
			sector = self.read_sector(sector_num)
			buf += sector
			
			end_marker_pos = buffer.find(b'__END__\n')
			if end_marker_pos != -1:
				buffer = buffer[:end_marker_pos]
				break

			sector_num += 1
			
		offset = 0
		
		while offset + ENTRY_SIZE <= len(buffer):
			entry_data = buffer[offset:offset + ENTRY_SIZE]
			filename = entry_data[:FILENAME_SIZE].rstrip(b'\x00').decode('utf-8')
			start_sector, size = struct.unpack('<II', entry_data[FILENAME_SIZE:])
			
			if filename:
				entries.append({
					'filename': filename,
					'start_sector': start_sector,
					'size': size
				})
				
			offset += ENTRY_SIZE
			
		return entries