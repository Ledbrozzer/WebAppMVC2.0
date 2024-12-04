function uploadFiles(callback) {
    const veiculoFileInput = document.getElementById('veiculoFile');
    const abastecimentoFileInput = document.getElementById('abastecimentoFile');
    const veiculoFile = veiculoFileInput.files[0];
    const abastecimentoFile = abastecimentoFileInput.files[0];

    if (!veiculoFile || !abastecimentoFile) {
        alert('Por favor, selecione ambos os arquivos.');
        return;
    }

    const formData = new FormData();
    formData.append('veiculoFile', veiculoFile);
    formData.append('abastecimentoFile', abastecimentoFile);

    fetch('/process_files', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Erro:', data.error);
            document.getElementById('results').innerHTML = 'Erro ao processar os dados: ' + data.error;
        } else {
            callback();
        }
    })
    .catch(error => console.error('Erro:', error));
}

function runAnalysis(endpoint) {
    uploadFiles(() => {
        fetch('/start_streamlit', {
            method: 'GET'
        })
        .then(() => {
            window.open('/' + endpoint, '_blank');
        })
        .catch(error => console.error('Erro:', error));
    });
}