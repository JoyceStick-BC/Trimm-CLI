import click
import requests
import zipfile
import os
import json
import shutil

from tqdm import tqdm


@click.group()
def cli():
    pass


@cli.command()
@click.option('--bundlename', prompt='Please enter your name/package', help='Your package name in format name/package.')
@click.option('--path', help='Absolute path to install packages. Defaults to currentDir/Assets/vendor.')
@click.option('--version', help='Version number for package.')
def install(bundlename, path, version):
    if not check_if_installed(bundlename, path, version):
        download(bundlename, version, path)


@cli.command()
@click.option('--bundlename', prompt='Please enter your name/package', help='Your package name in format name/package.')
@click.option('--path', help='Absolute path to locate info.json. Defaults to currentDir/Assets/vendor.')
@click.option('--version', help='Version number for package.')
def update(bundlename, path, version):
    if path is None:
        path = os.path.join(os.getcwd(), "Assets")
        path = os.path.join(path, "vendor")
        path += os.sep

    # if no version specified, assume latest
    if version is None:
        version = requests.get("http://snatch-it.org/latest/" + bundlename).json()["latest-version"]

    with open(path + "snatch.json", 'r') as snatch_file:
        snatch_json = json.load(snatch_file)
        snatch_assets = snatch_json["assets"]
        snatch_packages = snatch_json["packages"]

        if bundlename in snatch_assets:
            if not check_if_installed(bundlename, path, version):
                download(bundlename, version, path)
        elif bundlename in snatch_packages:
            if not check_if_installed(bundlename, path, version):
                download(bundlename, version, path)


# installs unzipped package to the given directory
def download(bundlename, version, path):
    # url = "http://snatch-it.org/" + bundlename + "/download"
    url = "http://fallingkingdom.net/" + bundlename + ".zip"
    if version is not None:
        url += "/" + version

    print("Downloading " + bundlename + "!")
    returned_request = requests.get(url, stream=True)
    total_size = int(returned_request.headers.get('content-length', 0))/(32*1024)

    with open('output.bin', 'wb') as f:
        for data in tqdm(returned_request.iter_content(32 * 1024), total=total_size, unit='B', unit_scale=True):
            f.write(data)

    # make sure web response is good before continuing
    if returned_request.status_code != 200:
        print("Bad response for url: %s" % url)
        os.remove("output.bin")
        return

    # make sure we have a zip file
    if not zipfile.is_zipfile("output.bin"):
        print("Returned file is not a zip at url: %s" % url)
        os.remove("output.bin")
        return

    print("Successfully downloaded " + bundlename + "!")

    # create a zipfile object
    zip_file = zipfile.ZipFile("output.bin")

    # set extract path
    if path is None:
        path = os.path.join(os.getcwd(), "Assets")
        if not os.path.exists(path):
            os.makedirs(path)
        path = os.path.join(path, "vendor")
        if not os.path.exists(path):
            os.makedirs(path)

    # get root snatch info.json if it exists, else create one
    snatch_path = os.path.join(path, "snatch.json")
    snatch_json = {"assets": {}, "packages": {}}
    if os.path.isfile(snatch_path):
        data_file = open(snatch_path, 'r')
        snatch_json = json.load(data_file)
    snatch_assets = snatch_json["assets"]
    snatch_packages = snatch_json["packages"]

    downloading_path = os.path.join(path, "downloading")
    zip_file.extractall(downloading_path)

    # let's delete the old bundle if it exists
    bundle_path = os.path.join(path, bundlename)
    if os.path.exists(bundle_path):
        shutil.rmtree(bundle_path)

    info_jsons = []
    drill(downloading_path, path, info_jsons)

    # let's go over all the jsons and add them to our snatch.json
    for info_json in info_jsons:
        if info_json["type"] == "asset":
            snatch_assets[bundlename] = info_json["version"]  # TODO could have multiple bundlenames, so loop through this
        elif info_json["type"] == "package":
            snatch_packages[bundlename] = info_json["version"]

    # delete the downloading folder and output.bin
    os.remove("output.bin")
    shutil.rmtree(downloading_path)

    # dump json
    with open(snatch_path, 'w+') as out_file:
        json.dump(snatch_json, out_file, indent=4, sort_keys=True)

    print("Successfully installed " + bundlename + "!")


def drill(bundle_path, vendor_path, info_jsons):
    # let's get all the files in the downloading path
    for filename in os.listdir(bundle_path):
        new_path = os.path.join(bundle_path, filename)
        # if we find a directory
        if os.path.isdir(new_path):
            # let's look for zips in this dir by identifying any info.jsons
            for unzipped_filename in os.listdir(new_path):
                inner_dir_path = os.path.join(new_path, unzipped_filename)
                # if we find an info.json, let's unzip it's associated zip
                if unzipped_filename == "info.json":
                    # add the info to our list of info jsons
                    inner_data_file = open(inner_dir_path, 'r')
                    inner_info_json = json.load(inner_data_file)
                    info_jsons.append(inner_info_json)

                    # if this bundle is an asset
                    if inner_info_json["type"] == "asset":
                        # let's extract the asset zip to the vendor path
                        inner_asset_path = os.path.join(new_path, inner_info_json["name"] + ".zip")  # need to change bundlename to name for fk testing TODO add something to folder name if version is static
                        print("Unzipping " + inner_info_json["bundlename"] + "!")
                        inner_zip_file = zipfile.ZipFile(inner_asset_path)

                        bundle_vendor_path = os.path.join(vendor_path, inner_info_json["username"])
                        if not os.path.exists(bundle_vendor_path):
                            os.makedirs(bundle_vendor_path)
                        inner_zip_file.extractall(bundle_vendor_path)

                        # after extracting zip, let's delete
                        os.remove(inner_asset_path)

                    # if this bundle is a package
                    elif inner_info_json["type"] == "package":
                        # let's extract all the bundles of this package
                        for unzipped_package_filename in os.listdir(new_path):
                            inner_package_file = os.path.join(new_path, unzipped_package_filename)

                            # let's extract the inner bundle zips to this dir
                            if zipfile.is_zipfile(inner_package_file):
                                inner_zip_file = zipfile.ZipFile(inner_package_file)
                                inner_zip_file.extractall(new_path)

                                # after extracting zip, let's delete
                                os.remove(inner_package_file)

                        # now let's drill again to handle the bundles of the package
                        drill(new_path, vendor_path, info_jsons)


def check_if_installed(bundlename, path, requested_version):
    # if no version specified, assume latest
    if requested_version is None:
        requested_version = requests.get("http://snatch-it.org/latest/" + bundlename).json()["latest-version"]

    if path is None:
        path = os.path.join(os.getcwd(), "Assets")
        path = os.path.join(path, "vendor")
        path += os.sep

    snatch_path = os.path.join(path, "snatch.json")
    snatch_json = {"assets": {}, "packages": {}}
    if os.path.isfile(snatch_path):
        data_file = open(snatch_path, 'r')
        snatch_json = json.load(data_file)
    snatch_assets = snatch_json["assets"]
    snatch_packages = snatch_json["packages"]

    version = None

    if bundlename in snatch_assets:
        version = snatch_assets[bundlename]
    elif bundlename in snatch_packages:
        version = snatch_packages[bundlename]

    if version is not None:
        if version == requested_version:
            print("Requested version of " + bundlename + " is already installed! Skipping...")
            return True

        print("Version " + version + " of the bundle named " + bundlename
              + " already exists! (To keep both bundles, cancel this operations and use 'snatch install " + bundlename
              + " --v=" + str(requested_version) + "*')")
        response = raw_input("Do you want to update this bundle to version " + str(requested_version) + "? (y/n)")
        if response == "n":
            return True

    return False


if __name__ == '__main__':
    cli()
