const urlParts = window.location.pathname.split('/');
const dbName = urlParts[1];

const tableSelect = document.getElementById('table-select');
const createTableContainer = document.getElementById('create-table-container');
const confirmCreateTableBtn = document.getElementById('confirm-create-table');
const addColumnBtn = document.getElementById('add-column-btn');
const addColumnForm = document.getElementById('add-column-form');
const addRowBtn = document.getElementById('add-row-btn');
const addRowForm = document.getElementById('add-row-form');


function addTableToSelector(tableName) {
    const option = document.createElement('option');
    option.value = tableName;
    option.textContent = tableName;
    tableSelect.appendChild(option);
}

document.addEventListener('DOMContentLoaded', () => {
    confirmCreateTableBtn.addEventListener('click', () => {
        const tableName = document.getElementById('table-name').value;
        if (tableName) {
            createTable(dbName, tableName);
            createTableContainer.style.display = 'none';
        } else {
            alert('Please enter a table name.');
        }
    });

    addColumnBtn.addEventListener('click', () => {
        $('#addColumnModal').modal('show');
    });

    addColumnForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const columnName = document.getElementById('column-name').value;
        const columnType = document.getElementById('column-type').value;
        console.log(`Adding column: ${columnName}, Type: ${columnType}`);
        addColumnToTable(columnName, columnType);
        $('#addColumnModal').modal('hide');
    });

    async function createTable(dbName, tableName) {
        const response = await fetch(`/${dbName}/${tableName}/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        if (response.ok) {
            addTableToSelector(tableName);
            tableSelect.value = tableName;
        } else {
            alert('Failed to create database');
        }
        loadTableData(tableName);
    }

    function loadTableData(tableName) {
        if (!tableName) {
            clearTableData();
            return;
        }

        fetch(`/${dbName}/${tableName}/rows`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log(data)
                populateTable(data.rows, data.columns);
            })
            .catch(error => {
                console.error('Error fetching table data:', error);
                clearTableData();
            });
    }

    function populateTable(data, columns) {
        const tableHeader = document.getElementById('table-header');
        const tableBody = document.getElementById('table-body');
        const rowActions = document.getElementById('row-actions');

        rowActions.innerHTML = '';
        tableHeader.innerHTML = '';
        tableBody.innerHTML = '';

        columns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            th.style.cursor = 'pointer';

            th.addEventListener('click', () => {
                const confirmDelete = confirm(`Ви дійсно хочете видалити колонку "${col}"?`);
                if (confirmDelete) {
                    deleteColumn(col);
                }
            });
            tableHeader.appendChild(th);
        });

        if (data.length > 0) {

            const actionDiv = document.createElement('div');
            actionDiv.setAttribute('data-row-id', "");
            actionDiv.style.display = 'flex';
            actionDiv.style.alignItems = 'center';
            actionDiv.style.height = `38px`;
            actionDiv.style.marginBottom = '2px';

            rowActions.appendChild(actionDiv);

            data.forEach(row => {
                const tr = document.createElement('tr');
                tr.setAttribute('data-row-id', row.id);

                columns.forEach(col => {
                    const td = document.createElement('td');
                    td.textContent = row.values[col] === null ? '' : row.values[col];
                    tr.appendChild(td);
                });

                tableBody.appendChild(tr);

                const actionDiv = document.createElement('div');
                actionDiv.setAttribute('data-row-id', row.id);
                actionDiv.style.display = 'flex';
                actionDiv.style.alignItems = 'center';
                actionDiv.style.height = `${tr.offsetHeight}px`;
                actionDiv.style.marginBottom = '2px';

                const deleteBtn = document.createElement('button');
                deleteBtn.textContent = 'D';
                deleteBtn.className = 'action-btn';
                deleteBtn.addEventListener('click', () => {
                    const confirmDelete = confirm(`Ви дійсно хочете видалити цей рядок?`);
                    if (confirmDelete) {
                        deleteRow(row.id);
                    }
                });

                const editBtn = document.createElement('button');
                editBtn.textContent = 'E';
                editBtn.className = 'action-btn';
                editBtn.addEventListener('click', () => {
                    editRow(row.id);
                });
                actionDiv.appendChild(deleteBtn);
                actionDiv.appendChild(editBtn);
                rowActions.appendChild(actionDiv);
            });
        }
    }


    async function fetchTables(dbName) {
        try {
            const response = await fetch(`/${dbName}/tables`);
            if (response.ok) {
                const data = await response.json();
                populateTableSelect(data.tables, tableSelect);
            } else {
                alert('Failed to load tables.');
            }
        } catch (error) {
            console.error('Error fetching tables:', error);
        }
    }

    function removeDefaultOption() {
        const defaultOption = tableSelect.querySelector('option[value=""]');
        if (defaultOption) {
            tableSelect.removeChild(defaultOption);
        }
    }


    tableSelect.addEventListener('change', function () {
        const selectedTable = this.value;
        if (selectedTable === 'create') {
            createTableContainer.style.display = 'block';
        } else if (selectedTable) {
            createTableContainer.style.display = 'none';
            loadTableData(selectedTable);
        }
        removeDefaultOption();
    });
    fetchTables(dbName);

    async function addColumnToTable(columnName, columnType) {
        try {
            const url = `/${dbName}/${tableSelect.value}/add_column?column_name=${encodeURIComponent(columnName)}&column_type=${encodeURIComponent(columnType)}`;

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                const th = document.createElement('th');
                th.textContent = columnName;
                document.getElementById('table-header').appendChild(th);

                const tableRows = document.querySelectorAll('#table-body tr');
                tableRows.forEach(row => {
                    const td = document.createElement('td');
                    td.textContent = '';
                    row.appendChild(td);
                });
            } else {
                const errorData = await response.json();
                alert(`Не вдалося додати колонку: ${errorData.detail}`);
            }
        } catch (error) {
            console.error('Error adding column:', error);
            alert('Виникла помилка при додаванні колонки.');
        }
    }

    function createSubmitButton(id) {
        const submitButton = document.createElement('button');
        submitButton.type = 'submit';
        submitButton.className = 'btn btn-primary mt-3';
        submitButton.textContent = 'Submit';
        submitButton.id = id
        return submitButton;
    }

    addRowBtn.addEventListener('click', async () => {
        addRowForm.innerHTML = '';

        const placeholderMap = {
            "integer": "example: 123",
            "real": "example: 123.45",
            "char": "Single character",
            "string": "text",
            "time": "HH:MM:SS",
            "timeInvl": "HH:MM:SS-HH:MM:SS"
        };

        try {
            const response = await fetch(`/${dbName}/${tableSelect.value}/get_columns`);
            if (response.ok) {
                const data = await response.json();
                const columns = Object.entries(data)
                console.log("Columns:", columns)
                columns.forEach(([columnName, columnType]) => {
                    const div = document.createElement('div');
                    div.className = 'mb-3';
                    const label = document.createElement('label');
                    label.textContent = columnName;
                    label.className = 'form-label';
                    const input = document.createElement('input');
                    input.type = 'text';
                    input.className = 'form-control';
                    input.id = `input-${columnName}`;
                    input.placeholder = placeholderMap[columnType] || '';
                    div.appendChild(label);
                    div.appendChild(input);
                    addRowForm.appendChild(div);
                });
                const submitButton = createSubmitButton(0);
                addRowForm.appendChild(submitButton);
                $('#addRowModal').modal('show');
            }
        } catch (error) {
            console.error('Error fetching tables:', error);
        }
    })

    addRowForm.addEventListener('submit', async () => {
        event.preventDefault();

        const submitButton = addRowForm.querySelector('button[type="submit"]');
        console.log(submitButton.id)
        if (submitButton.id !== '0') {
            await editRowSubmit(submitButton.id)
        } else {
            const rowData = {
                values: {}
            };

            document.querySelectorAll('#add-row-form input').forEach(input => {
                const columnName = input.id.replace('input-', '');
                rowData.values[columnName] = input.value.trim() === '' ? null : input.value;
            });
            console.log(rowData)

            try {
                const response = await fetch(`/${dbName}/${tableSelect.value}/add_row`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(rowData),
                });

                if (response.ok) {
                    $('#addRowModal').modal('hide');
                    loadTableData(tableSelect.value);
                } else {
                    const error = await response.json();
                    alert(error.detail)
                    $('#addRowModal').modal('show');
                    console.error('Error adding row:', error.detail);
                }
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }
    });

    async function deleteColumn(columnName) {
        const response = await fetch(`/${dbName}/${tableSelect.value}/delete_column?column_name=${columnName}`, {
            method: 'DELETE'
        });
        if (response.ok) {
            loadTableData(tableSelect.value);
        }
    }

    async function deleteRow(rowId) {
        const response = await fetch(`/${dbName}/${tableSelect.value}/delete_row?row_id=${rowId}`, {
            method: 'DELETE'
        });
        if (response.ok) {
            loadTableData(tableSelect.value);
        }
    }

    async function editRow(rowId) {
        addRowForm.innerHTML = '';

        const placeholderMap = {
            "integer": "example: 123",
            "real": "example: 123.45",
            "char": "Single character",
            "string": "text",
            "time": "HH:MM:SS",
            "timeInvl": "HH:MM:SS-HH:MM:SS"
        };

        try {
            const columnsResponse = await fetch(`/${dbName}/${tableSelect.value}/get_columns`);
            if (columnsResponse.ok) {
                const columnsData = await columnsResponse.json();
                const columns = Object.entries(columnsData)
                console.log("Columns:", columns)
                const rowResponse = await fetch(`/${dbName}/${tableSelect.value}/row/${rowId}`);
                if (rowResponse.ok) {
                    const rowData = await rowResponse.json();
                    console.log("RowData:", rowData)
                    document.getElementById('addRowModalLabel').textContent = 'Edit Row';
                    columns.forEach(([columnName, columnType]) => {
                        console.log(rowData[columnName])
                        console.log(columnName)
                        const div = document.createElement('div');
                        div.className = 'mb-3';
                        const label = document.createElement('label');
                        label.textContent = columnName;
                        label.className = 'form-label';
                        const input = document.createElement('input');
                        input.type = 'text';
                        input.className = 'form-control';
                        input.id = `input-${columnName}`;
                        input.placeholder = placeholderMap[columnType] || '';
                        input.value = (rowData && rowData[columnName]) ? rowData[columnName] : '';

                        div.appendChild(label);
                        div.appendChild(input);
                        addRowForm.appendChild(div);
                    });
                } else {
                    throw new Error('Error fetching row data');
                }
            } else {
                throw new Error('Error fetching columns');
            }

            const submitButton = createSubmitButton(rowId);
            addRowForm.appendChild(submitButton);

            $('#addRowModal').modal('show');
        } catch (error) {
            console.error('Error:', error);
        }
    }


    async function editRowSubmit(rowId) {
        event.preventDefault();

        const rowData = {
            values: {}
        };

        document.querySelectorAll('#add-row-form input').forEach(input => {
            const columnName = input.id.replace('input-', '');
            rowData.values[columnName] = input.value.trim() === '' ? null : input.value;
        });

        try {
            const response = await fetch(`/${dbName}/${tableSelect.value}/row/${rowId}/edit`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(rowData),
            });

            if (response.ok) {
                $('#addRowModal').modal('hide');
                loadTableData(tableSelect.value);
            } else {
                const error = await response.json();
                alert(error.detail);
                $('#addRowModal').modal('show');
                console.error('Error editing row:', error.detail);
            }
        } catch (error) {
            console.error('Error submitting edit:', error);
        }
    }
});


async function deleteTable() {
    const selectedTable = tableSelect.value;
    if (!selectedTable || selectedTable === 'create') {
        alert('Please select a table to delete.');
        return;
    }

    const confirmDelete = confirm(`Are you sure you want to delete the table "${selectedTable}"?`);
    if (confirmDelete) {
        const response = await fetch(`/${dbName}/${selectedTable}/delete`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (response.ok) {
            removeTableFromSelector(selectedTable);
            addDefaultSelectOption();
            clearTableData();
        } else {
            alert('Failed to delete the table.');
        }
    }
}

function addDefaultSelectOption() {
    if (!Array.from(tableSelect.options).some(option => option.value === '')) {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = '-- Select or Create a Table --';
        tableSelect.prepend(option);
    }
    tableSelect.value = '';
}

function clearTableData() {
    const tableHeader = document.getElementById('table-header');
    const tableBody = document.getElementById('table-body');
    tableHeader.innerHTML = '';
    tableBody.innerHTML = '';
}

function removeTableFromSelector(tableName) {
    const options = tableSelect.options;
    for (let i = 0; i < options.length; i++) {
        if (options[i].value === tableName) {
            tableSelect.remove(i);
            break;
        }
    }
}


function populateTableSelect(tables, selector) {
    tables.forEach(table => {
        const option = document.createElement('option');
        option.value = table;
        option.textContent = table;
        selector.appendChild(option);
    });
}

document.getElementById('find-difference-btn').addEventListener('click', async () => {
    try {
        const response = await fetch(`/${dbName}/tables`);
        if (response.ok) {
            const data = await response.json();
            const table1Select = document.getElementById('table1Select');
            const table2Select = document.getElementById('table2Select');
            table1Select.options.length = 0;
            table2Select.options.length = 0;
            populateTableSelect(data.tables, table1Select);
            populateTableSelect(data.tables, table2Select);
            $('#compareTablesModal').modal('show');
        }
    } catch (error) {
        console.error('Error fetching tables:', error);
    }
});

document.getElementById('compareTablesSubmit').addEventListener('click', async () => {
    const table1 = document.getElementById('table1Select').value;
    const table2 = document.getElementById('table2Select').value;

    try {
        const response = await fetch(`/${dbName}/${table1}/compare/${table2}`);
        if (response.ok) {
            const result = await response.json();
            const {rows, columns} = result;
            $('#compareTablesModal').modal('hide');
            showComparisonResult(rows, columns);
        } else {
            const error = await response.json();
            alert(`Error comparing tables: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error comparing tables:', error);
    }
});


function showComparisonResult(data, data_col) {
    const tableHeader = document.getElementById('comparison-table-header');
    const tableBody = document.getElementById('comparison-table-body');

    tableHeader.innerHTML = '';
    tableBody.innerHTML = '';
    console.log(data)

    const columns = Object.entries(data_col);
    console.log("Columns:", columns)

    const headerRow = document.createElement('tr');
    columns.forEach(([columnName, columnType]) => {
        const th = document.createElement('th');
        th.textContent = columnName;
        headerRow.appendChild(th);
    });
    tableHeader.appendChild(headerRow);

    data.forEach(row => {
        const tr = document.createElement('tr');
        columns.forEach(([columnName, columnType]) => {
            const td = document.createElement('td');
            td.textContent = row[columnName] === null ? '' : row[columnName];
            tr.appendChild(td);
        });
        tableBody.appendChild(tr);
    });
    $('#comparisonResultModal').modal('show');
}















