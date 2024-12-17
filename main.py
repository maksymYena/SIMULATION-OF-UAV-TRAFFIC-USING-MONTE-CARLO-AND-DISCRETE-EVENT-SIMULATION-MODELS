import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

# Ініціалізація графа зон
zones = {
    'A': {'pos': (0, 0), 'density': 0.9},
    'B': {'pos': (1, 1), 'density': 0.2},
    'C': {'pos': (2, 0), 'density': 0.3},
    'D': {'pos': (1, -1), 'density': 0.5},
    'E': {'pos': (3, 1), 'density': 0.4},
}

# Гранична щільність
max_density = 0.6

# Створення графу зон
G = nx.Graph()
for zone, info in zones.items():
    G.add_node(zone, pos=info['pos'], density=info['density'])
    for other_zone in zones:
        if zone != other_zone:
            distance = np.linalg.norm(np.array(info['pos']) - np.array(zones[other_zone]['pos']))
            if distance < 2:  # З'єднуємо сусідні зони
                G.add_edge(zone, other_zone)

# Журнал перенаправлень для збереження інформації про перенаправлення
reroute_log = []


# Клас БПЛА для відстеження шляху
class UAV:
    def __init__(self, id, start_zone):
        self.id = id
        self.current_zone = start_zone
        self.path = [start_zone]

    def reroute(self, available_zones):
        # Знаходимо нову зону з мінімальною щільністю
        new_zone = min(available_zones, key=lambda z: zones[z]['density'])

        # Додаємо запис до журналу перенаправлень
        reroute_log.append({
            'uav_id': self.id,
            'from_zone': self.current_zone,
            'to_zone': new_zone,
            'density_from': zones[self.current_zone]['density'],
            'density_to': zones[new_zone]['density']
        })

        # Оновлюємо поточну зону та шлях БПЛА
        self.current_zone = new_zone
        self.path.append(new_zone)


# Ініціалізація БПЛА
uavs = [UAV(i, 'A') for i in range(3)]  # Створимо 3 БПЛА, які починають у зоні 'A'

# Виконуємо перенаправлення для кожного БПЛА
for uav in uavs:
    if zones[uav.current_zone]['density'] > max_density:
        # Знайти зони з допустимою щільністю
        available_zones = [z for z in zones if zones[z]['density'] <= max_density]
        if available_zones:
            uav.reroute(available_zones)

# Виведення журналу перенаправлень
print("Журнал перенаправлень:")
for entry in reroute_log:
    print(f"БПЛА {entry['uav_id']} перенаправлений з {entry['from_zone']} до {entry['to_zone']} "
          f"(щільність: {entry['density_from']} -> {entry['density_to']})")

# Візуалізація графа після перенаправлення
plt.figure(figsize=(8, 6))
pos = nx.get_node_attributes(G, 'pos')
nx.draw(G, pos, with_labels=True,
        node_color=['red' if zones[zone]['density'] > max_density else 'green' for zone in zones], node_size=700)

# Додаємо підписи до зон із щільністю
zone_labels = {zone: f"{zone}\nDensity: {info['density']}" for zone, info in zones.items()}
nx.draw_networkx_labels(G, pos, labels=zone_labels)

# Відображаємо траєкторії БПЛА
colors = ['blue', 'purple', 'orange']
for idx, uav in enumerate(uavs):
    path_edges = [(uav.path[i], uav.path[i + 1]) for i in range(len(uav.path) - 1)]
    nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color=colors[idx], width=2)

plt.title("Система зон з траєкторіями перенаправлень БПЛА та щільністю зон")
plt.show()
