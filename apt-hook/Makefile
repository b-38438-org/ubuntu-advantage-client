all: hook

build: hook

hook: hook.cc
	$(CXX) -Wall -Wextra -pedantic $(CXXFLAGS) $(CPPFLAGS) $(LDFLAGS) -g -o hook hook.cc -lapt-pkg $(LDLIBS)

install: hook
	install -D -m 644 20apt-esm-hook.conf $(DESTDIR)/etc/apt/apt.conf.d/20apt-esm-hook.conf
	install -D -m 755 hook $(DESTDIR)/usr/lib/ubuntu-advantage/apt-esm-hook

clean:
	rm -f hook
