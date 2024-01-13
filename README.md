# img_miner

### Build docker image

```bash
make image PLATFORM=x86
```

### Run

1. Run normally:

```bash
python img_miner/miner.py
```

2. Run using a docker container:

```bash
docker run -d \
 --name image-miner \
 -v "${PWD}:/mounted" \
 docker.io/library/image_miner:arm64-latest \
   image-miner --save_dir /mounted/mined_images
```
