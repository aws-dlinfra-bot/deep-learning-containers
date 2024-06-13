import os
import re

import pytest
import yaml

from test.test_utils import is_pr_context, get_repository_local_path, LOGGER


@pytest.mark.quick_checks
@pytest.mark.model("N/A")
@pytest.mark.integration("release_images_training.yml")
@pytest.mark.skipif(
    not is_pr_context(),
    reason="This test is only needed to validate release_images configs in PRs.",
)
def test_release_images_training_yml():
    _release_images_yml_verifier(image_type="training", excluded_image_type="inference")


@pytest.mark.quick_checks
@pytest.mark.model("N/A")
@pytest.mark.integration("release_images_inference.yml")
@pytest.mark.skipif(
    not is_pr_context(),
    reason="This test is only needed to validate release_images configs in PRs.",
)
def test_release_images_inference_yml():
    _release_images_yml_verifier(image_type="inference", excluded_image_type="training")


@pytest.mark.quick_checks
@pytest.mark.model("N/A")
@pytest.mark.integration("release_images_patches.yml")
@pytest.mark.skipif(
    not is_pr_context(),
    reason="This test is only needed to validate release_images configs in PRs.",
)
def test_release_images_patches_yml():
    dlc_base_dir = get_repository_local_path()

    release_images_yml_file = os.path.join(dlc_base_dir, "release_images_patches.yml")

    with open(release_images_yml_file, "r") as release_imgs_handle:
        for line in release_imgs_handle:
            assert (
                "force_release: True" not in line
            ), f"Force release is not permitted in patch file {release_images_yml_file}."


@pytest.mark.quick_checks
@pytest.mark.model("N/A")
@pytest.mark.integration("release_images_numbering")
@pytest.mark.skipif(
    not is_pr_context(),
    reason="This test is only needed to validate release_images configs in PRs.",
)
def test_release_images_numbering():
    release_yamls = [
        "release_images_patches.yml",
        "release_images_training.yml",
        "release_images_inference.yml",
    ]
    dlc_base_dir = get_repository_local_path()

    for release_yaml in release_yamls:
        yaml_path = os.path.join(dlc_base_dir, release_yaml)

        with open(yaml_path, "r") as rf:
            contents = yaml.safe_load(rf)
            for i, (num, imgs) in enumerate(contents["release_images"].items()):
                if i + 1 != int(num):
                    LOGGER.error(
                        f"Numbering seems incorrect in {release_yaml}. Try updating to the following:"
                    )
                    counter = 1
                    with open(yaml_path, "r") as debugger:
                        for line in debugger:
                            if re.match(r"^\s{2}\d+:", line):
                                LOGGER.info(f"  {counter}:"),
                                counter += 1
                            else:
                                LOGGER.info(line.strip("\n") if line else line),
                    raise RuntimeError(
                        f"Line {i+1} in {release_yaml} is numbered incorrectly as {num}. Please correct the ordering."
                    )


@pytest.mark.quick_checks
@pytest.mark.model("N/A")
@pytest.mark.integration("release_images_no_overlaps")
@pytest.mark.skipif(
    not is_pr_context(),
    reason="This test is only needed to validate release_images configs in PRs.",
)
def test_release_images_no_overlaps():
    release_yamls = [
        "release_images_patches.yml",
        "release_images_training.yml",
        "release_images_inference.yml",
    ]
    dlc_base_dir = get_repository_local_path()

    configs = []

    for release_yaml in release_yamls:
        yaml_path = os.path.join(dlc_base_dir, release_yaml)

        with open(yaml_path, "r") as rf:
            contents = yaml.safe_load(rf)
            for num, imgs in contents["release_images"].items():
                if imgs in configs:
                    raise RuntimeError(
                        f"Found duplicate configs for {imgs} in {release_yaml}. These could be coming from another release yaml or the same file - please double check."
                    )
                configs.append(imgs)


def _release_images_yml_verifier(image_type, excluded_image_type):
    """
    Simple test to ensure release images yml file is loadable
    Also test that excluded_image_type is not present in the release yml file
    """
    dlc_base_dir = get_repository_local_path()

    release_images_yml_file = os.path.join(dlc_base_dir, f"release_images_{image_type}.yml")

    # Define exclude regex
    exclude_pattern = re.compile(rf"{excluded_image_type}", re.IGNORECASE)

    with open(release_images_yml_file, "r") as release_imgs_handle:
        for line in release_imgs_handle:
            assert not exclude_pattern.search(
                line
            ), f"{exclude_pattern.pattern} found in {release_images_yml_file}. Please ensure there are not conflicting job types here."
        try:
            yaml.safe_load(release_imgs_handle)
        except yaml.YAMLError as e:
            raise RuntimeError(
                f"Failed to load {release_images_yml_file} via pyyaml package. Please check the contents of the file, correct errors and retry."
            ) from e
