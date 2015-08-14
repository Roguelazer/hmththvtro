hmththvtro.html: data cache/legislators-current.json cache/legislators-historical.json hmththvtro.tmpl process.py requirements
	env/bin/python process.py cache > $@

.PHONY: clean
clean:
	rm -f hmththvtro.html cache

.PHONY: data
data: requirements
	bash get_data.sh cache

env:
	virtualenv env/

.PHONY: requirements
requirements: env
	env/bin/pip install -r requirements.txt
