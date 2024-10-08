function showCreateInput() {
    const dbNameContainer = document.getElementById('db-name-container');
    dbNameContainer.style.display = 'block';
}

async function createDatabase() {
    const dbName = document.getElementById('db-name').value;
    if (!dbName) {
        alert('Please enter a database name');
        return;
    }

    const response = await fetch(`/${dbName}/create`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    });
    if (response.ok) {
        window.location.href = `/${dbName}`;
    } else {
        alert('Failed to create database');
    }
}


document.addEventListener('DOMContentLoaded', () => {
    function fetchDatabases() {
        fetch('/all_databases')
            .then(response => response.json())
            .then(data => {
                const databases = data.databases;
                populateDatabaseList(databases);
            })
            .catch(error => {
                console.error('Error fetching databases:', error);
            });
    }

    function populateDatabaseList(databases) {
        const dbListContainer = document.getElementById('databases-list');
        dbListContainer.innerHTML = '';
        databases.forEach(db => {
            const dbItem = document.createElement('div');
            dbItem.classList.add('db-item');

            dbItem.innerHTML = `
                <a href="/${db}">
                    <h5>${db}</h5>
                </a>
            `;
            dbListContainer.appendChild(dbItem);
        });
    }
    //
    fetchDatabases();
});
