import matplotlib.pyplot as plt
import io

# строим графики прогресса по воде и калориям, сохраняем в картинку
def generate_progress_chart(water_logged, water_goal, cal_logged, cal_goal):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    ax1.bar(['Выпито', 'Цель'], [water_logged, water_goal], color=['#3498db', '#bbf'])
    ax1.set_title('Прогресс по воде (мл)')

    ax2.bar(['Потреблено', 'Цель'], [cal_logged, cal_goal], color=['#e74c3c', '#fbb'])
    ax2.set_title('Прогресс по калориям (ккал)')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.clf()
    return buf