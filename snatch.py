import click


@click.command()
@click.option('--name', prompt="Please enter your name/package", help='The person to greet.')
def pull(name):
    click.echo('Hello %s!' % name)


if __name__ == '__main__':
    pull()
