.PHONY: build run remove_containers remove_images

build:
	podman build -t marinetraffic .

run:
	podman run -v ./data:/app/data --rm marinetraffic

remove_containers:
	podman container ls -a | awk 'NR>1 { print $1 }' | xargs podman rm

remove_images:
	podman images | awk 'NR>1 { print $3 }' | xargs podman rmi
