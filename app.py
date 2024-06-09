from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# In-memory storage for simplicity
books = []
members = []
transactions = []

# Book Management


@app.route('/books', methods=['GET'])
def get_books():
    return jsonify(books)


@app.route('/books', methods=['POST'])
def add_book():
    book = request.json
    books.append(book)
    return jsonify(book), 201


@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    book = next((b for b in books if b['id'] == book_id), None)
    if book:
        book.update(request.json)
        return jsonify(book)
    return jsonify({"error": "Book not found"}), 404


@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    global books
    books = [b for b in books if b['id'] != book_id]
    return jsonify({"message": "Book deleted"})

# Member Management


@app.route('/members', methods=['GET'])
def get_members():
    return jsonify(members)


@app.route('/members', methods=['POST'])
def add_member():
    member = request.json
    members.append(member)
    return jsonify(member), 201


@app.route('/members/<int:member_id>', methods=['PUT'])
def update_member(member_id):
    member = next((m for m in members if m['id'] == member_id), None)
    if member:
        member.update(request.json)
        return jsonify(member)
    return jsonify({"error": "Member not found"}), 404


@app.route('/members/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    global members
    members = [m for m in members if m['id'] != member_id]
    return jsonify({"message": "Member deleted"})

# Transactions


@app.route('/issue', methods=['POST'])
def issue_book():
    transaction = request.json
    book = next((b for b in books if b['title']
                == transaction['book_title']), None)
    member = next(
        (m for m in members if m['id'] == transaction['member_id']), None)
    if book and member and book['stock'] > 0:
        book['stock'] -= 1
        transaction['type'] = 'issue'
        transactions.append(transaction)
        return jsonify(transaction)
    return jsonify({"error": "Book not available or member not found"}), 400


@app.route('/return', methods=['POST'])
def return_book():
    transaction = request.json
    book = next((b for b in books if b['title']
                == transaction['book_title']), None)
    member = next(
        (m for m in members if m['id'] == transaction['member_id']), None)
    if book and member:
        book['stock'] += 1
        transaction['type'] = 'return'
        transactions.append(transaction)
        # Handle rent fee and debt
        member['debt'] += transaction['rent_fee']
        if member['debt'] > 500:
            return jsonify({"error": "Member's outstanding debt exceeds Rs.500"}), 400
        return jsonify(transaction)
    return jsonify({"error": "Book or member not found"}), 400


@app.route('/search', methods=['GET'])
def search_books():
    title = request.args.get('title')
    author = request.args.get('author')
    result = [b for b in books if (title in b['title'] if title else True) and (
        author in b['author'] if author else True)]
    return jsonify(result)

# Data Import


@app.route('/import', methods=['POST'])
def import_books():
    num_books = int(request.json.get('num_books', 20))
    title = request.json.get('title')
    authors = request.json.get('authors')
    publisher = request.json.get('publisher')
    page = request.json.get('page')

    # Frappe API endpoint
    frappe_api_url = 'https://frappe.io/api/method/frappe-library'
    params = {
        'title': title,
        'authors': authors,
        'publisher': publisher,
        'page': page
    }

    imported_books = []
    while num_books > 0:
        response = requests.get(frappe_api_url, params=params)
        data = response.json()
        books_to_import = data['message'][:min(num_books, 20)]
        for book in books_to_import:
            book_record = {
                'title': book['title'],
                'author': book['authors'],
                'isbn': book['isbn'],
                'publisher': book['publisher'],
                'stock': 1,  # Default stock as 1 for imported books
                'available': True
            }
            books.append(book_record)
            imported_books.append(book_record)
        num_books -= len(books_to_import)
        params['page'] = int(params.get('page', 1)) + 1

    return jsonify(imported_books), 201


if __name__ == '__main__':
    app.run(debug=True)
