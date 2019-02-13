import os

import github
import click


@click.command()
@click.option("--organization", type=str, required=True)
@click.option("--path-in-repo", type=str, required=True)
@click.option("--existing-file", type=click.Path(exists=True), required=True)
@click.option("--new-file", type=click.Path(exists=True), required=True)
@click.option("--commit-message", type=str, required=True)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--do-once", is_flag=True, default=False)
@click.pass_context
def cli(
    ctx,
    organization,
    path_in_repo,
    existing_file,
    new_file,
    commit_message,
    dry_run=False,
    do_once=False,
):
    gh = github.Github(os.environ["GITHUB_API_TOKEN"])

    with open(existing_file, "r") as f:
        contents_to_match = f.read()

    with open(new_file, "r") as f:
        new_contents = f.read()

    for repo in gh.get_organization(organization).get_repos():
        if repo.archived:
            click.secho(f"{repo.full_name}: skipping archived repo", color="yellow")
            continue

        try:
            existing_github_file = repo.get_file_contents(path_in_repo)
            existing_contents = existing_github_file.decoded_content
        except Exception as e:
            click.secho(
                f"{repo.full_name}: error getting {path_in_repo} {e}", fg="yellow"
            )
            continue

        click.secho(f"{repo.full_name}: contents of {path_in_repo}", fg="cyan")
        click.secho(existing_contents.decode("utf-8"))

        existing_str_stripped = existing_contents.strip().decode("utf-8")

        if existing_str_stripped == new_contents.strip():
            click.secho(f"{repo.full_name}: contents already match the new version!", fg="green")
            continue

        if existing_str_stripped != contents_to_match.strip():
            click.secho(
                f"{repo.full_name}: contents do not match the expected",
                fg="red",
            )
            continue

        if dry_run:
            click.secho("(not updating in dry run)")
        else:
            repo.update_file(
                path_in_repo, commit_message, new_contents, existing_github_file.sha
            )
            click.secho(
                f"{repo.full_name}: successfully updated {path_in_repo}", fg="green"
            )

        if do_once:
            click.secho("Exiting after first success because of --do-once")
            exit(0)


if __name__ == "__main__":
    cli()
