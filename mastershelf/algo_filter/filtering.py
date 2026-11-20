from mastershelf.recipes.preprocessing import *
from mastershelf.inventory.inventory import *
from mastershelf.algo_filter.recommendation import *
import re
from google.cloud import bigquery
import json


def get_matching_recipes(user_ingredients_list: dict, pantry_items: list, user_dict: dict) -> list[dict]:
    client = bigquery.Client()

    user_inventory = pantry_items

    # Clean et suppression des valeurs vides/espaces
    user_inv_cleaned = [
        k.lower().strip() for k in user_inventory if k and k.strip()
    ]
    print("1 - On récupère l'inventaire du placard", user_inv_cleaned)

    raw_ingredients = user_ingredients_list.get("ingredients_list", [])
    cleaned_input = [
        ing.lower().strip() for ing in raw_ingredients if ing and ing.strip()
    ]
    print("1bis - On récupère l'inventaire de la photo", cleaned_input)

    # Fusion des listes en minuscules
    combined_ingredients = list(set(user_inv_cleaned) | set(cleaned_input))
    print("1ter - On fusionne les deux inventaires", combined_ingredients)

    print("2 - On lance la query !")

    query = """
      WITH user_ingredients AS (
          SELECT DISTINCT LOWER(TRIM(ing)) AS ing
          FROM UNNEST(@user_ing_list) AS ing
      )

      SELECT *
      FROM `le-wagon-ds-2327.mastershelf.recipes` r

      WHERE ARRAY_LENGTH(r.ingredients_clean) > 0
          AND NOT EXISTS (
          SELECT 1
          FROM UNNEST(r.ingredients_clean) AS recipe_ing
          WHERE LOWER(TRIM(recipe_ing)) NOT IN (
          SELECT ing
          FROM user_ingredients
          )
      )

      LIMIT 20;
    """

    #J'ai changé la query pour trouver un exact match , sinon eggplant = egg , maintenat que tout est catégorisé c'est plus rapide
    # et le chemin vers le nouveau dataset propre final

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter(
                "user_ing_list", "STRING", combined_ingredients
            )
        ]
    )
    print("1")
    query_job = client.query(query, job_config=job_config)
    print("2")
    df = query_job.to_dataframe()
    print("3")

    # results = query_job.result()
    results = predict_closer(user_dict, df)
    print("4")

    print("Résultat de predict Closer : ", results)

    print("3 - On retourne les résultats !")

    recipes = []
    for row in results:
        recipe = dict(row)
        raw_steps = recipe.get("steps")

        # Conversion de la string Python (ex: "['étape 1', 'étape 2']") en liste
        if isinstance(raw_steps, str):
            try:
                recipe["steps"] = ast.literal_eval(raw_steps)
            except (ValueError, SyntaxError):
                recipe["steps"] = [raw_steps]

        recipes.append(recipe)

    return results


# # Exemple d'appel de la fonction :
# if __name__ == "__main__":
#     ingredients_test = ['celery', 'carrot', 'onion', 'olive oil', 'chicken', 'milk', 'cheese']
#     recipes = get_matching_recipes(ingredients_test)

#     print(f"Nombre de recettes trouvées : {len(recipes)}")
#     if recipes:
#         print("Première recette :", recipes[0]["name"])

def final_match(photo_ingredient):
    """
    Charge le dataset , importe la photo et l'inventaire pour trouver les correspondances
    """
    data = load_recipes()
    user_inventory = get_user_inv()
    available_names = list(set(set(user_inventory.keys()) | set(photo_ingredient["ingredients_list"])))
    top_recipes = data.copy()
    print("Finding matches ...")
    top_recipes["coverage"] = top_recipes["ingredients"].apply(lambda x: recipe_coverage(x, available_names))
    top_recipes["n_ingredients"] = top_recipes["ingredients"].apply(len)

    possible_recipes = (
        top_recipes[top_recipes["coverage"] == 1.0]
        .sort_values(
            by=["coverage", "n_ingredients"],
            ascending=[False, False]
        )
    )

    possible_recipes[["name","steps","coverage", "n_ingredients"]].head(10)
    return possible_recipes.iloc[0].steps

def get_user_inv():
    """
    Récupère l'inventaire de l'utilisateur , sinon par défaut
    """

    inventory = None
    # streamlit case à cocher
    if inventory:
        return inventory
    return  USER_INV

def recipe_coverage(recipe_ingredients, user_ingredients):
    """
    Calculer le coverage des ingrédients
    """
    if len(recipe_ingredients) == 0:
        return 0

    matches = 0

    for recipe_ing in recipe_ingredients:
        found = any(
            ingredient_match(user_ing, recipe_ing)
            for user_ing in user_ingredients
        )

        if found:
            matches += 1

    return matches / len(recipe_ingredients)

def ingredient_match(user_ing, recipe_ing):
    """
    Regarder les similarités
    """
    user_ing = user_ing.lower().strip()
    recipe_ing = recipe_ing.lower().strip()

    return (
        re.search(rf"\b{re.escape(user_ing)}\b", recipe_ing)
        is not None
    )
