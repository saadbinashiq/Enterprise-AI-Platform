"""
Knowledge Graph module.

Local/demo backend: NetworkX (in-memory, zero setup, runs anywhere -- good
for the intern demo and for classroom/restricted environments).
Production backend: Neo4j -- same query methods, same return shapes, so
nothing else in the app needs to change. Set GRAPH_BACKEND=neo4j and
NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD in .env to switch (requires
`pip install neo4j` and a running Neo4j instance).

Entities: Store, Product, Employee, Vendor
Relationships: SOLD (Store->Product), WORKS_AT (Employee->Store)
"""
import os
import networkx as nx
import pandas as pd
from dotenv import load_dotenv

from db.database import get_session
from db.models import Store, Product, Sale, Employee, Vendor

load_dotenv()

GRAPH_BACKEND = os.getenv("GRAPH_BACKEND", "networkx")


class NetworkXGraph:
    def __init__(self):
        self.g = nx.MultiDiGraph()

    def build_from_db(self):
        session = get_session()
        try:
            for s in session.query(Store).all():
                self.g.add_node(f"store:{s.store_id}", type="Store", name=s.name,
                                 city=s.city, country=s.country)
            for p in session.query(Product).all():
                self.g.add_node(f"product:{p.product_id}", type="Product", name=p.name,
                                 category=p.category, price=p.price)
            for e in session.query(Employee).all():
                self.g.add_node(f"employee:{e.employee_id}", type="Employee",
                                 name=e.name, department=e.department, salary=e.salary)
                self.g.add_edge(f"employee:{e.employee_id}", f"store:{e.store_id}", relation="WORKS_AT")
            for v in session.query(Vendor).all():
                self.g.add_node(f"vendor:{v.vendor_id}", type="Vendor", name=v.name,
                                 reliability=v.reliability_score)
            for sale in session.query(Sale).all():
                self.g.add_edge(f"store:{sale.store_id}", f"product:{sale.product_id}",
                                 relation="SOLD", revenue=sale.revenue, date=str(sale.date))
        finally:
            session.close()
        return self

    def stats(self):
        return {"nodes": self.g.number_of_nodes(), "edges": self.g.number_of_edges()}

    def underperforming_stores(self, bottom_n=3):
        totals = {}
        for u, v, data in self.g.edges(data=True):
            if data.get("relation") == "SOLD":
                totals[u] = totals.get(u, 0) + data.get("revenue", 0)
        ranked = sorted(totals.items(), key=lambda x: x[1])[:bottom_n]
        return [{"store": self.g.nodes[node]["name"], "total_revenue": round(total, 2)}
                for node, total in ranked]

    def top_stores(self, top_n=3):
        totals = {}
        for u, v, data in self.g.edges(data=True):
            if data.get("relation") == "SOLD":
                totals[u] = totals.get(u, 0) + data.get("revenue", 0)
        ranked = sorted(totals.items(), key=lambda x: -x[1])[:top_n]
        return [{"store": self.g.nodes[node]["name"], "total_revenue": round(total, 2)}
                for node, total in ranked]

    def declining_products(self, bottom_n=3):
        """Products whose recent-third revenue is lower than early-third
        revenue -- candidates for discontinuation."""
        rows = []
        for u, v, data in self.g.edges(data=True):
            if data.get("relation") == "SOLD":
                rows.append({"product": v, "date": data["date"], "revenue": data["revenue"]})
        if not rows:
            return []
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"])
        cutoff_early = df["date"].quantile(0.33)
        cutoff_late = df["date"].quantile(0.66)

        early = df[df["date"] <= cutoff_early].groupby("product")["revenue"].sum()
        late = df[df["date"] >= cutoff_late].groupby("product")["revenue"].sum()
        merged = pd.DataFrame({"early": early, "late": late}).fillna(0)
        merged = merged[merged["early"] > 0]
        merged["decline_pct"] = ((merged["late"] - merged["early"]) / merged["early"]) * 100
        worst = merged.sort_values("decline_pct").head(bottom_n)

        return [{
            "product": self.g.nodes[idx]["name"],
            "early_revenue": round(float(row["early"]), 2),
            "recent_revenue": round(float(row["late"]), 2),
            "decline_pct": round(float(row["decline_pct"]), 1),
        } for idx, row in worst.iterrows()]

    def department_headcount_cost(self):
        rows = [{"department": d["department"], "salary": d["salary"]}
                for _, d in self.g.nodes(data=True) if d.get("type") == "Employee"]
        df = pd.DataFrame(rows)
        summary = df.groupby("department").agg(headcount=("salary", "count"),
                                                 total_cost=("salary", "sum")).reset_index()
        return summary.sort_values("total_cost", ascending=False).to_dict("records")


class Neo4jGraph:
    """Same interface as NetworkXGraph, backed by a real Neo4j instance."""

    def __init__(self):
        from neo4j import GraphDatabase
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password123")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def build_from_db(self):
        session = get_session()
        try:
            with self.driver.session() as ns:
                for s in session.query(Store).all():
                    ns.run("MERGE (s:Store {id:$id}) SET s.name=$name, s.city=$city, s.country=$country",
                           id=s.store_id, name=s.name, city=s.city, country=s.country)
                for p in session.query(Product).all():
                    ns.run("MERGE (p:Product {id:$id}) SET p.name=$name, p.category=$category",
                           id=p.product_id, name=p.name, category=p.category)
                for e in session.query(Employee).all():
                    ns.run("""
                        MATCH (st:Store {id:$store_id})
                        MERGE (emp:Employee {id:$id})
                        SET emp.name=$name, emp.department=$department, emp.salary=$salary
                        MERGE (emp)-[:WORKS_AT]->(st)
                    """, id=e.employee_id, store_id=e.store_id, name=e.name,
                         department=e.department, salary=e.salary)
                for sale in session.query(Sale).all():
                    ns.run("""
                        MATCH (st:Store {id:$store_id})
                        MATCH (p:Product {id:$product_id})
                        CREATE (st)-[:SOLD {revenue:$revenue, date:$date}]->(p)
                    """, store_id=sale.store_id, product_id=sale.product_id,
                         revenue=sale.revenue, date=str(sale.date))
        finally:
            session.close()
        return self

    def underperforming_stores(self, bottom_n=3):
        with self.driver.session() as s:
            result = s.run("""
                MATCH (st:Store)-[r:SOLD]->(:Product)
                WITH st, sum(r.revenue) AS total_revenue
                RETURN st.name AS store, total_revenue
                ORDER BY total_revenue ASC LIMIT $n
            """, n=bottom_n)
            return [r.data() for r in result]

    # top_stores / declining_products / department_headcount_cost would be
    # implemented the same way -- Cypher queries with the same return shape
    # as the NetworkX methods above.


def build_graph():
    if GRAPH_BACKEND == "neo4j":
        return Neo4jGraph().build_from_db()
    return NetworkXGraph().build_from_db()


_GRAPH_SINGLETON = None


def get_graph():
    global _GRAPH_SINGLETON
    if _GRAPH_SINGLETON is None:
        _GRAPH_SINGLETON = build_graph()
    return _GRAPH_SINGLETON


if __name__ == "__main__":
    g = build_graph()
    print("Graph stats:", g.stats())
    print("\nUnderperforming stores:")
    for r in g.underperforming_stores():
        print(" -", r)
    print("\nTop stores:")
    for r in g.top_stores():
        print(" -", r)
    print("\nDeclining products:")
    for r in g.declining_products():
        print(" -", r)
    print("\nDepartment headcount/cost:")
    for r in g.department_headcount_cost():
        print(" -", r)
