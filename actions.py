from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import mysql.connector
from rasa_sdk.events import SlotSet
from datetime import datetime



# Establecer conexión a la base de datos
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="12345",
    database="billetera"  # <- nombre de la base de datos
)

cursor = conn.cursor()

class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_hello_world"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        documento = tracker.get_slot("documento")

        if not documento:
            dispatcher.utter_message(text="No tengo tu documento aún. ¿Podrías proporcionarlo?")
            return []

        try:
            # Ejecutar la consulta en la tabla 'movimientos'
            cursor.execute("SELECT * FROM movimientos WHERE documento = %s", (documento,))
            resultados = cursor.fetchall()

            if resultados:
                fila = resultados[0]  # Primera fila del resultado
                valor = fila[4]       # Asegúrate de que este índice corresponde al dato que quieres mostrar
                dispatcher.utter_message(text=f"Tu documento {valor} ha sido validado!")
            else:
                dispatcher.utter_message(text="No se encontró información con ese documento.")

        except Exception as e:
            dispatcher.utter_message(text=f"Ocurrió un error al acceder a la base de datos: {e}")

        return []


class ActionRegistrarIngreso(Action):

    def name(self) -> Text:
        return "action_registrar_ingreso"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        documento = tracker.get_slot("documento")
        monto = tracker.get_slot("monto")

        if not documento or not monto:
            dispatcher.utter_message(text="Necesito tu documento y el monto para registrar el ingreso.")
            return []

        try:
            cursor.execute(
                "INSERT INTO movimientos (documento, tipo, monto) VALUES (%s, %s, %s)",
                (documento, "ingreso", monto)
            )
            conn.commit()
            dispatcher.utter_message(text=f"Se registró un ingreso de {monto} correctamente.")
        except Exception as e:
            dispatcher.utter_message(text=f"Ocurrió un error al registrar el ingreso: {e}")

        return [SlotSet("tipo_movimiento", "ingreso")]

class ActionRegistrarGasto(Action):

    def name(self) -> Text:
        return "action_registrar_gasto"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        documento = tracker.get_slot("documento")
        monto = tracker.get_slot("monto")

        if not documento or not monto:
            dispatcher.utter_message(text="Necesito tu documento y el monto para registrar el gasto.")
            return []

        try:
            cursor.execute(
                "INSERT INTO movimientos (documento, tipo, monto) VALUES (%s, %s, %s)",
                (documento, "gasto", monto)
            )
            conn.commit()
            dispatcher.utter_message(text=f"Se registró un gasto de {monto} correctamente.")
        except Exception as e:
            dispatcher.utter_message(text=f"Ocurrió un error al registrar el gasto: {e}")

        return [SlotSet("tipo_movimiento", "gasto")]


class ActionConsultarSaldo(Action):

    def name(self) -> Text:
        return "action_consultar_saldo"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        documento = tracker.get_slot("documento")

        if not documento:
            dispatcher.utter_message(text="Necesito tu documento para consultar el saldo.")
            return []

        try:
            cursor.execute("SELECT tipo, monto FROM movimientos WHERE documento = %s", (documento,))
            movimientos = cursor.fetchall()

            saldo = 0
            for tipo, monto in movimientos:
                if tipo == "ingreso":
                    saldo += monto
                elif tipo == "gasto":
                    saldo -= monto

            dispatcher.utter_message(text=f"Tu saldo actual es de {saldo} pesos.")
        except Exception as e:
            dispatcher.utter_message(text=f"Ocurrió un error al consultar el saldo: {e}")

        return []
    
class ActionRegistrarMovimiento(Action):
    def name(self) -> Text:
        return "action_registrar_movimiento"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        tipo = tracker.get_slot("tipo_movimiento")
        detalle = tracker.get_slot("detalle")
        monto = tracker.get_slot("monto")
        documento = tracker.get_slot("documento")

        if not all([tipo, detalle, monto, documento]):
            dispatcher.utter_message(text="Faltan datos para registrar el movimiento.")
            return []

        try:
            fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            query = """
                INSERT INTO movimientos (tipo_movimiento, detalle, monto, documento, fecha)
                VALUES (%s, %s, %s, %s, %s)
            """
            values = (tipo, detalle, monto, documento, fecha)
            cursor.execute(query, values)
            conn.commit()

            dispatcher.utter_message(
                text=f"¡Movimiento registrado! {tipo.capitalize()} de ${monto:.2f} por '{detalle}'."
            )
        except Exception as e:
            dispatcher.utter_message(text=f"Error al registrar el movimiento: {e}")

        return []