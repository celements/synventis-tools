#!/bin/bash
read -p "Enter GitHub username: " username
for project in celements synventis programmonline; do
echo "Fetching $PROJECT repositories..."
curl -s -u $username "https://api.github.com/orgs/$project/repos?page=1&per_page=100" | \
  grep "ssh_url" | awk '{print $2}' | sed -e 's:\"::g' -e 's:,$::' >> repo-list.txt
done
read -p "[ENTER] to start cloning. Change local repo names by adding it to the line in repo-list.txt"
cat repo-list.txt | while read url; do git clone $url; done
