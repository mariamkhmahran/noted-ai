# Tool Schema Documentation

> The implementation of the tools is in [app/tools.py](app/tools.py), while the specification array of all tools which is passed to the openAI client is in [tool_definitions.json](tool_definitions.json)

Each tool is implemented as a Python function that the LLM invokes via the OpenAI tool-calling API. Below is the specification for each tool including its purpose, parameters, and return signatures.

#### 1. `add_note` (equivilant to: `/POST`)

- **Purpose:** Creates a new note record in the database.
- **Parameters:**
  - `title` (string): The title of the note.
  - `body` (string): The main text content (Required, cannot be null).
  - `tags` (list of strings): Categories or keywords to associate with the note.
- **Return Type:** `dict` with a status (ERROR | SUCCESS) and message.

#### 2. `search_notes` (equivilant to: `/GET`)

- **Purpose:** Performs a multi-criteria search to retrieve specific notes.
- **Parameters:**
  - `keyword` (string, optional): A term to search for within titles and bodies.
  - `tags` (list, optional): Filter by a specific set of tags.
  - `start_date` / `end_date` (string, optional): Date filters in `YYYY-MM-DD` format.
  - `limit` (integer, default=20): The maximum number of results to return.
- **Return Type:** `list` of note objects or `dict` (Error status and message).

#### 3. `update_note` (equivilant to: `/PUT`)

- **Purpose:** Modifies an existing note identified by its ID.
- **Parameters:**
  - `note_id` (integer): The unique identifier of the note to modify.
  - `title` (string): The updated title.
  - `body` (string): The updated content.
  - `tags` (list): The updated set of tags.
- **Return Type:** `dict` with a status (ERROR | SUCCESS) and message.

#### 4. `delete_note` (equivilant to: `/DELETE`)

- **Purpose:** Removes one notes from the database.
- **Parameters:**
  - `id` (int): The note ID to delete.
  - `title` (str): The title of the note to delete.
- **Return Type:** `str`: A status message.

#### 5. `fetch_all` (equivilant to: `/GET`)

- **Purpose:** Retrieves a broad list of notes, useful for summarization or contradiction detection tasks.
- **Parameters:**
  - `limit` (integer, optional): Maximum notes to fetch.
  - `order` (string, default="ASC"): Sorting order by creation date.
- **Return Type:** `list` of note objects or `dict` (Error status and message)..
