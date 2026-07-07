document.querySelector('form').addEventListener('submit', async function (e) {
            e.preventDefault();

            const btn = document.querySelector('input[type="submit"]');
            btn.value = "Checking...";
            btn.disabled = true;

            const formData = new FormData();
            formData.append('file', document.querySelector('input[type="file"]').files[0]);
            formData.append('job_description', document.querySelector('textarea').value);

            const response = await fetch('http://127.0.0.1:5000/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.error) {
                document.getElementById('result').innerHTML = `<p style="color:red;">${data.error}</p>`;
                btn.value = "Submit";
                btn.disabled = false;
                return;
            }

            const color = data.Score >= 80 ? 'green' : data.Score >= 50 ? 'orange' : 'red';

            btn.value = "Submit";
            btn.disabled = false;

            document.getElementById('result').innerHTML = `
                <h2 style="color:${color}">Score: ${data.Score.toFixed(2)}%</h2>

                <p>Matched: ${data.KeyWord_exists.map(k => `<span class="keyword-match">${k}</span>`).join(' ')}</p>
                <p>Missing: ${data.KeyWord_not_exist.map(k => `<span class="keyword-miss">${k}</span>`).join(' ')}</p>

                <div>Skills:
                    <div class="progress-bar">
                        <div class="progress-fill" style="width:${data.section_scores.skills_score}%"></div>
                    </div>
                    ${data.section_scores.skills_score.toFixed(2)}%
                </div>

                <div>Projects:
                    <div class="progress-bar">
                        <div class="progress-fill" style="width:${data.section_scores.projects_score}%"></div>
                    </div>
                    ${data.section_scores.projects_score.toFixed(2)}%
                </div>

                <div>Education:
                    <div class="progress-bar">
                        <div class="progress-fill" style="width:${data.section_scores.education_score}%"></div>
                    </div>
                    ${data.section_scores.education_score.toFixed(2)}%
                </div>

                <h3>💡 Tips:</h3>
                ${data.Unmatched_keyword_tips.map(tip => `<div class="tip-card">• ${tip}</div>`).join('')}
            `;
        });