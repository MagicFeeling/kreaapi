.PHONY: build image train find-unsafe get-styles clean

build:
	docker compose build

image: build
	docker compose run --rm -e SCRIPT=infer.py kreaapi

train: build
	docker compose run --rm -e SCRIPT=train.py kreaapi

get-styles: build
	docker compose run --rm -e SCRIPT=get_styles.py kreaapi

find-unsafe: build
	docker compose run --rm -e SCRIPT=find_unsafe.py kreaapi

clean:
	docker compose down --remove-orphans
	rm -rf output/
