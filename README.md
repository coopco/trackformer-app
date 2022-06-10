# Trackformer App
## Install
Must unzip contents of `ant-finetune.zip` to `models/ant-finetune` before building Docker image.

### NotImplementedError: Cuda is not availabel

When building Docker image, Docker BuildKit can run into issues with cuda while compiling MultiScaleDeformableAttention.

You must disable BuildKit when building this image, i.e. `DOCKER_BUILDKIT=0 docker built -t coopco/trakformer-app:latest .`
