function get_titles() {
  # Get current date
  start_date=$(date +"%Y-%m-%d")

  # Get date in 5 days (works on both Linux and macOS)
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS (BSD date)
    end_date=$(date -v+20d +"%Y-%m-%d")
  else
    # Linux (GNU date)
    end_date=$(date -d "@$(($(date +%s) + 20 * 24 * 60 * 60))" +"%Y-%m-%d")
  fi

  # API url
  API_URL="https://www.hebcal.com/hebcal?cfg=json&v=1&F=on&i=on&start=${start_date}&end=${end_date}"
  # API_URL="https://localhost:8080/hebcal?cfg=json&v=1&F=on&i=on&start=${start_date}&end=${end_date}"
  # API_URL="http://hebcal-web:8080/hebcal?cfg=json&v=1&F=on&i=on&start=${start_date}&end=${end_date}"

  url="$API_URL"

  echo "Calling $url"
  response=$(curl -s -X GET "$url")

  titles=$(echo "$response" | jq -r '.items[] | .title')

}

add_task_for_title() {
  title="$1"
  # Creating task name
  task_name="Daf Yomi - ${title}"

  transformed_task_name=$(echo $(python ~/.scripts/number_to_gematria.py "$task_name"))
  # echo "transformed_task_name: $transformed_task_name"

  echo "task add +@dafyomi +@daily +next project:DafYomi \"$transformed_task_name\""

}

get_titles


# Go over all titles by line breaks
IFS=$'\n'
for title in $titles; do
  add_task_for_title "$title"
done
unset IFS

# echo "$titles"