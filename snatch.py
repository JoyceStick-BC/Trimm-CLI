import click
import requests
import io
import zipfile
import os
import json


@click.group()
def cli():
    pass


@cli.command()
@click.option('--bundlename', prompt='Please enter your name/package', help='Your package name in format name/package.')
@click.option('--path', help='Absolute path to install packages. Defaults to currentDir/Assets/vendor.')
@click.option('--version', help='Version number for package.')
def install(bundlename, path, version):
    url = "http://snatch-it.org/" + bundlename + "/download"
    if version is not None:
        url += "/" + version

    download(bundlename, url, path)


@cli.command()
@click.option('--path', help='Absolute path to locate info.json. Defaults to currentDir/Assets/vendor.')
def pull(path):
    if path is None:
        path = os.getcwd() + os.pathsep + "Assets" + os.pathsep + "vendor" + os.pathsep

    with open(path + "info.json") as data_file:
        data = json.load(data_file)
        for bundle in data["assets"]:
            download(bundle["bundlename"], "http://snatch-it.org/" + bundle["bundlename"] + "/download", path)


# installs unzipped package to the given directory
def download(bundlename, url, path):
    returned_request = requests.get(url)

    # make sure web response is good before continuing
    if returned_request.status_code != 200:
        print("Bad response for url: %s" % url)
        return

    # make sure we have a zip file
    byte_file = io.BytesIO(returned_request.content)
    if not zipfile.is_zipfile(byte_file):
        print("Returned file is not a zip at url: %s" % url)
        return

    # create a zipfile object
    zip_file = zipfile.ZipFile(byte_file)

    # set extract path
    if path is None:
        path = os.path.join(os.getcwd(), "Assets")
        if not os.path.exists(path):
            os.makedirs(path)
        path = os.path.join(path, "vendor")
        if not os.path.exists(path):
            os.makedirs(path)
        path += os.sep

    zip_file.extractall(path)

    # now let's unzip all the inner zips
    for filename in os.listdir(path):
        new_path = os.path.join(path, filename)
        if zipfile.is_zipfile(new_path):
            inner_zip_file = zipfile.ZipFile(new_path)
            inner_zip_file.extractall(path)
            os.remove(new_path)

    print("Successfully downloaded " + bundlename + "!")


if __name__ == '__main__':
    cli()
