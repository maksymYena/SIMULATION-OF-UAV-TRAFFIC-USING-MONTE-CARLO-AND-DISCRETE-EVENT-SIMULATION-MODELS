import heapq
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

# Параметри симуляції
MAX_REROUTES_PER_UAV = 100
MAX_SIMULATION_TIME = 200
WAIT_TIME_THRESHOLD = 30
ZONE_FILL_RATE = 0.005  # Швидкість заповнення кожної зони за одиницю часу

class UAV:
    def __init__(self, id, start_zone, end_zone, speed=1.0):
        self.id = id
        self.current_zone = start_zone
        self.end_zone = end_zone
        self.path = [start_zone]
        self.speed = speed
        self.reroutes = 0
        self.arrival_time = None
        self.wait_time = 0

    def reroute(self, zones, max_density):
        available_zones = [z for z in zones if z.density <= max_density and z != self.current_zone]
        if available_zones and self.reroutes < MAX_REROUTES_PER_UAV:
            # Вибір зони з найнижчою щільністю
            new_zone = min(available_zones, key=lambda z: z.density)
            self.path.append(new_zone)
            self.current_zone = new_zone
            self.reroutes += 1
            return new_zone
        return None  # Повертає None, якщо немає доступних зон для перенаправлення

class Zone:
    def __init__(self, id, pos, density=0, arrival_rate=ZONE_FILL_RATE):
        self.id = id
        self.pos = pos
        self.density = density
        self.arrival_rate = arrival_rate

    def update_density(self):
        self.density += self.arrival_rate
        self.density = min(self.density, 1.0)

def calculate_distance(zone1, zone2):
    return np.linalg.norm(np.array(zone1.pos) - np.array(zone2.pos))

def run_simulation(num_uavs, zones, max_density, reroute_enabled=True):
    events_queue = []
    uavs = [UAV(i, np.random.choice(zones), np.random.choice(zones)) for i in range(num_uavs)]
    total_reroutes = 0
    total_operations = 0
    max_time = 0
    total_wait_time = 0

    for uav in uavs:
        add_event(events_queue, 0, "start", uav)

    while events_queue:
        time, event_type, uav_id, uav = heapq.heappop(events_queue)
        total_operations += 1

        if time > MAX_SIMULATION_TIME:
            break

        # Оновлення щільності для кожної зони в кожен момент часу
        for zone in zones:
            zone.update_density()

        max_time = max(max_time, time)

        if uav.current_zone == uav.end_zone:
            uav.arrival_time = time
            continue

        if event_type == "start" or event_type == "move":
            if uav.current_zone.density > max_density:
                if reroute_enabled:
                    if uav.reroutes >= MAX_REROUTES_PER_UAV:
                        uav.wait_time += WAIT_TIME_THRESHOLD
                        total_wait_time += WAIT_TIME_THRESHOLD
                        add_event(events_queue, time + WAIT_TIME_THRESHOLD, "move", uav)
                    else:
                        new_zone = uav.reroute(zones, max_density)
                        if new_zone is not None:  # Якщо є зона для перенаправлення
                            total_reroutes += 1
                            distance = calculate_distance(uav.current_zone, new_zone)
                            reroute_time = distance / uav.speed
                            add_event(events_queue, time + reroute_time, "move", uav)
                        else:  # Якщо немає зони для перенаправлення
                            uav.wait_time += WAIT_TIME_THRESHOLD
                            total_wait_time += WAIT_TIME_THRESHOLD
                            add_event(events_queue, time + WAIT_TIME_THRESHOLD, "move", uav)
                else:
                    uav.wait_time += WAIT_TIME_THRESHOLD
                    total_wait_time += WAIT_TIME_THRESHOLD
                    add_event(events_queue, time + WAIT_TIME_THRESHOLD, "move", uav)
            else:
                uav.path.append(uav.current_zone)
                if uav.current_zone == uav.end_zone:
                    uav.arrival_time = time
                else:
                    add_event(events_queue, time + np.random.exponential(1), "move", uav)

    arrived_uavs = [uav for uav in uavs if uav.arrival_time is not None]
    avg_arrival_time = (sum(uav.arrival_time for uav in arrived_uavs) / len(arrived_uavs)) if arrived_uavs else None
    avg_wait_time = (total_wait_time / len(arrived_uavs)) if arrived_uavs else None

    return {
        "Total Reroutes": total_reroutes,
        "Total Time": max_time,
        "Total Operations": total_operations,
        "Avg Arrival Time": avg_arrival_time,
        "Avg Wait Time": avg_wait_time
    }, uavs

def add_event(queue, event_time, event_type, uav):
    heapq.heappush(queue, (event_time, event_type, uav.id, uav))

# Настройки зон і параметрів
zones = [Zone('A', (0, 0), 0.2), Zone('B', (1, 1), 0.3), Zone('C', (2, 0), 0.1), Zone('D', (1, -1), 0.4),
         Zone('E', (3, 1), 0.2)]
max_density = 0.5
num_uavs = 200

# Запуск симуляції
metrics_with_reroute, uavs_with_reroute = run_simulation(num_uavs, zones, max_density, reroute_enabled=True)
metrics_without_reroute, uavs_without_reroute = run_simulation(num_uavs, zones, max_density, reroute_enabled=False)

# Відображення результатів
df = pd.DataFrame([metrics_with_reroute, metrics_without_reroute], index=["With Rerouting", "Without Rerouting"])
print("Simulation Results:")
print(df)

# Відображення таблиці результатів
def show_table(df):
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.axis('off')
    table = ax.table(cellText=df.values, colLabels=df.columns, rowLabels=df.index, cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(5)
    table.scale(1, 1)
    plt.title("Simulation Results", fontsize=9, weight='bold')
    plt.show()

# Відображення графіків з метриками
def plot_paths_with_metrics(zones, uavs, title, total_wait_time, total_reroutes):
    G = nx.Graph()
    pos = {zone.id: zone.pos for zone in zones}

    for zone in zones:
        G.add_node(zone.id, pos=zone.pos)
        for other_zone in zones:
            if zone != other_zone:
                G.add_edge(zone.id, other_zone.id, weight=calculate_distance(zone, other_zone))

    plt.figure(figsize=(10, 8))
    colors = ['red' if zone.density > max_density else 'green' for zone in zones]
    nx.draw(G, pos, with_labels=True, node_color=colors, node_size=700)
    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)

    # Підрахунок дронів та очікування в кожній зоні
    zone_drone_counts = {zone.id: 0 for zone in zones}
    zone_wait_times = {zone.id: 0 for zone in zones}

    for uav in uavs:
        for zone in uav.path:
            zone_drone_counts[zone.id] += 1
            zone_wait_times[zone.id] += uav.wait_time

    for zone in zones:
        x, y = pos[zone.id]
        plt.text(x, y - 0.2, f"Drones: {zone_drone_counts[zone.id]}", fontsize=8, ha='center', color='blue')
        plt.text(x, y - 0.4, f"Wait Time: {zone_wait_times[zone.id]}", fontsize=8, ha='center', color='purple')

    plt.title(f"{title}\nTotal Wait Time: {total_wait_time}, Total Reroutes: {total_reroutes}", fontsize=12)
    plt.show()

# Виклик функцій для відображення таблиці та графіків
show_table(df)
plot_paths_with_metrics(zones, uavs_with_reroute, "Paths with Rerouting", metrics_with_reroute["Avg Wait Time"], metrics_with_reroute["Total Reroutes"])
plot_paths_with_metrics(zones, uavs_without_reroute, "Paths without Rerouting", metrics_without_reroute["Avg Wait Time"], metrics_without_reroute["Total Reroutes"])
