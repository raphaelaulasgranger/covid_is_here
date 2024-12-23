import streamlit as st
import pandas as pd 
# import numpy as np 
import folium
from branca.colormap import LinearColormap
import plotly.express as px
from datetime import datetime
from streamlit_folium import folium_static
# import matplotlib.pyplot as plt

# '''
# Data issues de 
# https://www.data.gouv.fr/fr/reuses/covid-sumeau/
# set utilisé : 
# https://www.data.gouv.fr/fr/datasets/r/2963ccb5-344d-4978-bdd3-08aaf9efe514
# '''


    
def load_df(path):

    # Chargement du fichier CSV
    df = pd.read_csv(path  + 'sumeau-indicateurs.csv',
                     sep = ';'
                     )
    return df
    
def load_geo(path):
    # Chargement des données

    geo = pd.read_csv (path + 
                       'sumeau-stations.csv', 
                      sep = ';' 
                      )
    return geo 

def preprocess_data(df, geo):
    # Prétraitement des données
    
    # fonctions
    def conversion_date(year_week):
        year, week = year_week.split('-S')
        # Créer une date à partir de l'année et du numéro de semaine
        date = datetime.strptime(f'{year}-{week}-1', "%Y-%W-%w")
        # Ajuster pour que la semaine commence le lundi
        return date - pd.Timedelta(days=date.weekday())
    
    
    ### geo
    # Pour chaque colonne à convertir :
    colonnes_geo =  geo.iloc[:,-2:].columns.tolist() 
    # [col for col in df[:, 1,-1].columns ]
    # print ( geo.info())
    
    for col in colonnes_geo:
        # geo[col] =  geo[col].astype ('str')
        geo[col] = geo[col].str.replace(',', '.')
        geo[col] = pd.to_numeric(geo[col], errors='coerce')
    # display( geo )
    # print (geo.info())
    # Pour chaque colonne à convertir :
    colonnes_mesures = df.iloc[:,1: ].columns.tolist() 
    # [col for col in df[:, 1,-1].columns ]
    
    
    ### df 
    for col in colonnes_mesures:
        df[col] = df[col].str.replace(',', '.')
        df[col] = pd.to_numeric(df[col], errors='coerce')
    # df = df.sort_values(by=['date'])
    # # df.iloc[:,1:].astype('float')
    # display( df.tail(5)) 

    # Conversion de la colonne de semaines en dates
    df['date'] = df['semaine'].apply(conversion_date)

    # Définir la colonne de date comme index
    df.set_index('date', inplace=True)

    # Trier l'index par ordre croissant
    df.sort_index(inplace=True)
    # display(df)
    
    colonnes_mesures_locales = colonnes_mesures[:-1]
    # print ( colonnes_mesures_locales, colonnes_mesures)
    moyennes_par_lieu = df[colonnes_mesures_locales].tail(3).mean()
    # display ( df[colonnes_mesures_locales].tail(3), moyennes_par_lieu)
    # Créer un nouveau DataFrame avec les moyennes
    df_moyennes = pd.DataFrame({'Lieu': moyennes_par_lieu.index, 'Moyenne': moyennes_par_lieu.values})

    
    
    # fusionner les données avec les informations géographiques
    geo_final = pd.merge(geo, df_moyennes, left_on='nom', right_on='Lieu')

    return ( df , geo_final )


def visualize_time_data(df):
    # colonnes_mesures = df.iloc[:,1: ].columns.tolist() 
    colonnes_mesures =["PARIS SEINE-CENTRE", "National_12", "MARSEILLE", "LYON - SAINT FONS"]
    # st.write( "df" , colonnes_mesures)
    df_display = df[colonnes_mesures]
    # Création du graphique
    fig = px.line(
        df_display, 
        x=df_display.index, 
        y=df_display.columns,
        title='concentration virale de SARS-CoV-2 en cg/L'
        )
    
    # Personnalisation du graphique
    fig.update_layout(
        width=1400,  # Largeur en pixels
        height=1000,  # Hauteur en pixels
        xaxis_title='Date',
        yaxis_title='Valeur',
        # legend_title='Variables',
        hovermode='x unified'
    )
    
    # Ajout de marqueurs pour une meilleure lisibilité
    fig.update_traces(mode='lines+markers')
    
    # Personnalisation des couleurs (optionnel)
    fig.update_traces(line=dict(width=1))  # Augmente l'épaisseur des lignes
    
    # Ajout de plages de sélection
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1a", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        )
    )
    
    # Affichage du graphique
    # fig.show()
    st.plotly_chart(fig, use_container_width=True)
    return 

def visualize_data(df_final):
    # Création des visualisations
    # Créer la carte choroplèthe
    m = folium.Map(location=[df_final['latitude'].mean(), df_final['longitude'].mean()], zoom_start=6)
    
    # Créer une échelle de couleurs
    colormap = LinearColormap(colors=['yellow', 'orange', 'red'], vmin=df_final['Moyenne'].min(), vmax=df_final['Moyenne'].max())
    df_final= df_final.dropna(axis = 0)
    # Ajouter les données à la carte
    for idx, row in df_final.iterrows():
        # print ( idx, row)
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=10,
            popup=f"Lieu: {row['Lieu']}<br>Moyenne: {row['Moyenne']:.2f}<br>Population: {row['population']}",
            color=colormap(row['Moyenne']),
            fill=True,
            fillColor=colormap(row['Moyenne']),
            fillOpacity=0.7
        ).add_to(m)
    
    # Ajouter la légende
    colormap.add_to(m)
    
    # Sauvegarder la carte
    #m.save("carte_choroplèthe_mesures.html")
    
    
    return m

def main():
    st.title("Suivi du Covid En France")
    st.write("Ce graphe utilise le jeu de données du dispositif national de surveillance des eaux usées (SUM’Eau)")
    st.write("Il pourrait être mis à jour automatiquement à partir des données si data.gouv travaillait sur une API" )
    st.write ( "mise à jour 2/10/24 ")
    st.write ( "mise à jour 24/10/24 ")
    st.write ( "mise à jour 31/10/24")
    st.write ( "mise à jour 07/11/24")
    path = './'
    df = load_df(path)
    geo= load_geo (path)
    
    df_final , geo_final = preprocess_data(df, geo)
    # st.write( df_final )
    st.write('Evolution des mesures de concentrations dans les eaux usées')
    visualize_time_data(df_final )
    st.write('Moyenne des 3 dernières mesures par site')
    folium_static(visualize_data(geo_final) ) 
    st.write( 'https://www.data.gouv.fr/fr/datasets/surveillance-du-sars-cov-2-dans-les-eaux-usees-sumeau/#/discussions')
    st.write( "version 1.1")
    st.write( "milestone et todo :")
    st.write ( '.  mise à jour auto à fiabiliser. ')
    st.write ( '.  prediction temporelle')
    st.write ( 'objectif : production au 15/10/2024 ')

if __name__ == "__main__":
    main()
