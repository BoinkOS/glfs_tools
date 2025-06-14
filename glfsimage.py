import struct
from math import ceil

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
			
			dir_sector = b'__END__\n' + b'\x00' * (SECTOR_SIZE - len(b'__END__\n'))
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
			
			end_marker_pos = buf.find(b'__END__\n')
			if end_marker_pos != -1:
				buf = buf[:end_marker_pos]
				break

			sector_num += 1
			
		offset = 0
		
		while offset + ENTRY_SIZE <= len(buf):
			entry_data = buf[offset:offset + ENTRY_SIZE]
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
		
	def get_directory_table_size(self):
		sector_num = 1
		buf = b''
		
		while True:
			sector = self.read_sector(sector_num)
			buf += sector

			end_marker_pos = buf.find(b'__END__\n')
			if end_marker_pos != -1:
				return end_marker_pos + len(b'__END__\n')
				
			sector_num += 1
				
	def find_first_file_sector(self):
		entries = self.parse_directory_table()
		if not entries:
			return None
		return min(entry['start_sector'] for entry in entries)
	
	def shift_file_data_forward(self, shift_bytes):
		entries = self.parse_directory_table()
		entries.sort(key=lambda e : e["start_sector"], reverse=True) 
		# /\  moving from back to front here to avoid putting the
		# |   entire disk into memory while shifting, and instead
		#	 shifting file by file, back to front.
		
		for entry in entries:
			old_offset = entry["start_sector"]*SECTOR_SIZE
			new_offset = old_offset + shift_bytes
			self.file.seek(old_offset)
			
			data = self.file.read(entry["size"])

			self.file.seek(old_offset)
			self.file.write(b'\x00' * entry["size"])
			
			self.file.seek(new_offset)
			self.file.write(data)
			
			entry["start_sector"] += shift_bytes // SECTOR_SIZE
			
		self._rewrite_directory_table(entries)
	
	def _rewrite_directory_table(self, entries):
		buf = b''
		for entry in entries:
			filename_bytes = entry['filename'].encode('utf-8').ljust(FILENAME_SIZE, b'\x00')
			entry_bytes = filename_bytes + struct.pack('<II', entry['start_sector'], entry['size'])
			buf += entry_bytes

		buf += b'__END__\n'

		if len(buf) % SECTOR_SIZE != 0:
			buf += b'\x00' * (SECTOR_SIZE - (len(buf) % SECTOR_SIZE))

		self.file.seek(SECTOR_SIZE)
		self.file.write(buf)
	
	def projected_directory_table_size(self, entry_count):
		size = entry_count * ENTRY_SIZE + len(b'__END__\n')
		if size % SECTOR_SIZE != 0:
			size += SECTOR_SIZE - (size % SECTOR_SIZE)
		return size
		
	def add_file(self, src_path, dest_filename):
		with open(src_path, 'rb') as f:
			file_data = f.read()

		entries = self.parse_directory_table()
		dir_table_size = self.get_directory_table_size()

		first_file_sector = self.find_first_file_sector()
		if first_file_sector is None:
			first_file_sector = ceil((dir_table_size + SECTOR_SIZE - 1) / SECTOR_SIZE)  # next free sector after dir table

		needed_dir_space = ENTRY_SIZE

		projected_size = self.projected_directory_table_size(len(entries) + 1)  # +1 for the new entry
		projected_dir_end = SECTOR_SIZE + projected_size
		first_file_offset = first_file_sector * SECTOR_SIZE

		if projected_dir_end > first_file_offset:
			print('Not enough space in the directory table. Shifting files forward...')
			
			required_shift_bytes = projected_dir_end - first_file_offset
			required_shift_sectors = ceil(required_shift_bytes / SECTOR_SIZE)
			
			self.shift_file_data_forward(required_shift_sectors * SECTOR_SIZE)
			
			entries = self.parse_directory_table()
			dir_table_size = self.get_directory_table_size()
			first_file_sector = self.find_first_file_sector()
			if first_file_sector is None:
				first_file_sector = (dir_table_size + SECTOR_SIZE - 1) // SECTOR_SIZE

			dir_end_offset = dir_table_size
			first_file_offset = first_file_sector * SECTOR_SIZE

		# recompute in case we shifted
		entries = self.parse_directory_table()
		used_sectors = set()
		for entry in entries:
			for sector in range(entry['start_sector'], entry['start_sector'] + (entry['size'] + SECTOR_SIZE - 1) // SECTOR_SIZE):
				used_sectors.add(sector)

		current_sector = ceil((projected_size + SECTOR_SIZE - 1) / SECTOR_SIZE)
		
		while current_sector in used_sectors:
			current_sector += 1
		
		self.file.seek(current_sector * SECTOR_SIZE)
		self.file.write(file_data)

		entries.append({
			"filename": dest_filename,
			"start_sector": current_sector,
			"size": len(file_data)})
		self._rewrite_directory_table(entries)


		print(f'Added file: {dest_filename} at sector {current_sector}')
		
	def extract_file(self, filename, output_path):
		entries = self.parse_directory_table()
	
		for entry in entries:
			if entry['filename'] == filename:
				start = entry['start_sector'] * SECTOR_SIZE
				size = entry['size']
			
				self.file.seek(start)
				data = self.file.read(size)
			
				with open(output_path, 'wb') as out_file:
					out_file.write(data)
			
				print(f'Extracted "{filename}" to "{output_path}"')
				return
	
		print(f'File "{filename}" not found in image.')