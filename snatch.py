import click
import requests
import io
import zipfile


@click.command()
@click.option('--name', prompt='Please enter your name/package', help='Your package name in format name/package.')
@click.option('--path', help='Absolute path to install packages. Defaults to current dir.')
@click.option('--version', help='Version number for package.')
def pull(name, path, version):
    url = "http://snatch.joycestick.com/api/" + name
    if version is not None:
        url += "/" + version

    download(url, path)


# installs unzipped package to the given directory
def download(url, path):
    returned_request = requests.get(url)

    # make sure web response is good before continuing
    if returned_request.status_code != 200:
        print("Bad response for url: %s" % url)
        return

    byte_file = io.BytesIO(returned_request.content)
    if not zipfile.is_zipfile(byte_file):
        print("Returned file is not a zip at url: %s" % url)
        return

    # create a zipfile object
    zip_file = zipfile.ZipFile(byte_file)

    # extract zip
    if path is not None:
        zip_file.extractall(path)
    else:
        zip_file.extractall()

    print("Success!")


if __name__ == '__main__':
    pull()
