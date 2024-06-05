#ifndef clox_table_h
#define clox_table_h

#include "common.h"
#include "value.h"


typedef struct {
    ObjString* key;
    Value value;
} Entry;


typedef struct {
    int count;
    int capacity;
    Entry* entries;
} Table;

void initTable(Table* table);
void freeTable(Table* table);

bool tableSet(Table* table, ObjString* key, Value value);
bool tableGet(Table* table, ObjString* key, Value* value);
bool tableDelete(Table* table, ObjString* key);
Entry* findEntry(Entry* entries, int capacity, ObjString* key);

ObjString* tableFindString(Table* table, const char* chars, int length, uint32_t hash);

static void adjustCapacity(Table* table, int capacity);
void tableAddAll(Table* from, Table* to);

#endif