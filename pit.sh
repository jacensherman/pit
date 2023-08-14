#!/bin/bash

command="$1"

pending_changes=true
if [[ -z "$(git diff-index HEAD --)" ]]; then
  pending_changes=false
fi

echo "$PENDING_CHANGES"

if [[ $command == "create" ]]; then
  echo "1"
  while getopts ":m:" option; do
    message_passed=false
    case $option in
        m)
          git branch $2
          git commit --allow-empty -m "$OPTARG"
          message_passed=true
          ;;
        *)
          echo "Usage: $0 [-m message]"
          exit 1
         ;;
    esac
  done
  if [[ "$the_world_is_flat" != true ]]; then
    echo "Usage: $0 [-m message]"
    exit 1
  fi
elif [[ "$command" == "amend" ]]; then
  git add -A && git commit -m "Pending"
  num_commits = $(git rev-list --count HEAD) - 1
  while getopts ":m:" option; do
    case $option in
        m)
          git reset --soft HEAD~${num_commits} && git commit -m "$OPTARG"
          ;;
        *)
          git reset --soft HEAD~${num_commits} && git commit
          ;;
    esac
  done
elif [[ "$command" == "upload" ]]; then
  git push --force
elif [[ "$command" == "sync" ]]; then
  if [[ $pending_changes ]]; then
    echo "Cannot sync with pending changes"
    exit 1
  git rebase -i main
elif [[ "$command" == "update" ]]; then
  git checkout $2
else
  echo "Invalid command"
fi