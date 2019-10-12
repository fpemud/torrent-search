prefix=/usr

all:

install:
	install -d -m 0755 "$(DESTDIR)/$(prefix)/bin"
	install -m 0755 torrent-search "$(DESTDIR)/$(prefix)/bin"

	install -d -m 0755 "$(DESTDIR)/$(prefix)/lib64/torrent-search"
	cp -r lib/* "$(DESTDIR)/$(prefix)/lib64/torrent-search"
	find "$(DESTDIR)/$(prefix)/lib64/torrent-search" -type f | xargs chmod 644
	find "$(DESTDIR)/$(prefix)/lib64/torrent-search" -type d | xargs chmod 755

	install -d -m 0755 "$(DESTDIR)/$(prefix)/share"
	cp -r share/* "$(DESTDIR)/$(prefix)/share"
	# find "$(DESTDIR)/$(prefix)/share/fpemud-refsystem" -type f | xargs chmod 644
	# find "$(DESTDIR)/$(prefix)/share/fpemud-refsystem" -type d | xargs chmod 755

.PHONY: all install
