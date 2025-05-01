IPTV Config Handler - README

Program Flow:
1. Start by creating a .cfg file from your .m3u playlist.
2. Edit the .cfg file manually.
3. Use --sort to clean and categorize the config based on 'category-id'.

Category-ID Mapping:
- 0: Unsorted
- 1: Live Channels
- 2: Movies
- 3: Series
- 4: 4K Movies
- 5: Box Sets
- 6: Live Sports
- 7: Kids Movies
- 8: Kids Series
- 9: Music Events
- 10: 24/7 Channels
- 99: Favorites

Example Usage:
- Create config: python cfg-handler.py -i iptv.m3u -c output.cfg
- Sort config:   python cfg-handler.py --sort -c output.cfg
